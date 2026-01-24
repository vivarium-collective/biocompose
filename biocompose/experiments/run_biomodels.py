"""
Load BioModels entries, extract UniformTimeCourse settings from SED-ML,
resolve SBML source, and emit process-bigraph documents for UTC steps.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import biomodels
import libsedml

from process_bigraph import allocate_core  # Composite optional depending on your runner


# ----------------------------
# Data structures
# ----------------------------

@dataclass(frozen=True)
class UniformTimeCourseSpec:
    initial_time: float
    output_start_time: float
    output_end_time: float
    number_of_points: int

    @property
    def duration(self) -> float:
        return float(self.output_end_time - self.output_start_time)


@dataclass(frozen=True)
class BiomodelLoadResult:
    biomodel_id: str
    sbml_path: str               # local file path
    sedml_path: str              # local file path
    utc: UniformTimeCourseSpec   # parsed from SED-ML


# ----------------------------
# Helpers: picking files
# ----------------------------

_SBML_RE = re.compile(r"\.(xml|sbml)$", re.IGNORECASE)
_SEDML_RE = re.compile(r"\.sedml$", re.IGNORECASE)


def _iter_entry_files(entry: Any) -> Iterable[Any]:
    """
    BioModels library return shapes can vary; this tries to normalize.

    We accept:
      - a list of file entries
      - metadata dict containing something list-like under 'files'/'main_files'
      - the raw object already iterable
    """
    if entry is None:
        return []

    if isinstance(entry, list) or isinstance(entry, tuple):
        return entry

    if isinstance(entry, dict):
        for key in ("files", "main_files", "model_files"):
            v = entry.get(key)
            if isinstance(v, (list, tuple)):
                return v
        # fall through: maybe dict isn't the right thing
        return []

    # last resort: if it's iterable, try it
    try:
        return list(entry)
    except TypeError:
        return []


def _file_name(obj: Any) -> str:
    # entries often have .name; otherwise treat as str
    return getattr(obj, "name", str(obj))


def find_first_sedml(entry_files: Iterable[Any]) -> Optional[Any]:
    for f in entry_files:
        name = _file_name(f)
        if _SEDML_RE.search(name):
            return f
    return None


def find_first_sbml(entry_files: Iterable[Any]) -> Optional[Any]:
    # Prefer SBML-ish xml that is NOT sedml and not obvious “manifest”
    candidates = []
    for f in entry_files:
        name = _file_name(f)
        if _SEDML_RE.search(name):
            continue
        if _SBML_RE.search(name):
            candidates.append(f)

    # Heuristic: prefer names containing "sbml" or "model"
    for key in ("sbml", "model"):
        for c in candidates:
            if key in _file_name(c).lower():
                return c

    return candidates[0] if candidates else None


# ----------------------------
# SED-ML parsing
# ----------------------------

def read_sedml_doc(sedml_path: str) -> libsedml.SedDocument:
    doc = libsedml.readSedMLFromFile(str(sedml_path))
    if doc is None:
        raise RuntimeError(f"libsedml returned None reading: {sedml_path}")
    if doc.getNumErrors() > 0:
        # keep this strict; you can loosen if needed
        msg = doc.getErrorLog().toString()
        raise RuntimeError(f"SED-ML parse errors in {sedml_path}:\n{msg}")
    return doc


def extract_first_uniform_time_course(sed_doc: libsedml.SedDocument) -> UniformTimeCourseSpec:
    """
    Finds the first UniformTimeCourse simulation in the doc and returns its settings.
    More robust than checking type codes, since python bindings vary.
    """
    n_sims = int(sed_doc.getNumSimulations())
    for i in range(n_sims):
        sim = sed_doc.getSimulation(i)
        if sim is None:
            continue

        # Robustly detect a UniformTimeCourse:
        # - in many bindings there is isSedUniformTimeCourse()
        # - otherwise check for the attribute/methods that only UTC has
        is_utc = False

        if hasattr(sim, "isSedUniformTimeCourse"):
            try:
                is_utc = bool(sim.isSedUniformTimeCourse())
            except Exception:
                is_utc = False

        if not is_utc:
            # Fallback heuristic: UTC has these getters
            needed = ("getInitialTime", "getOutputStartTime", "getOutputEndTime", "getNumberOfPoints")
            is_utc = all(hasattr(sim, m) for m in needed)

        if not is_utc:
            continue

        init_t = float(sim.getInitialTime())
        out_start = float(sim.getOutputStartTime())
        out_end = float(sim.getOutputEndTime())
        n_pts = int(sim.getNumberOfPoints())

        return UniformTimeCourseSpec(
            initial_time=init_t,
            output_start_time=out_start,
            output_end_time=out_end,
            number_of_points=n_pts,
        )

    raise ValueError("No UniformTimeCourse simulation found in SED-ML.")



def resolve_sbml_source_from_sedml(
    sed_doc: libsedml.SedDocument,
    sedml_dir: str,
    fallback_sbml_path: str,
) -> str:
    """
    Many SED-ML docs reference the SBML via Model.source (relative path or URL).
    We try to resolve a local path if it’s relative to the SED-ML file directory.
    If it’s a URL or missing, we fallback to the SBML we found in the BioModels entry.
    """
    if sed_doc.getNumModels() == 0:
        return fallback_sbml_path

    model = sed_doc.getModel(0)
    if model is None:
        return fallback_sbml_path

    src = model.getSource()  # string
    if not src:
        return fallback_sbml_path

    # If it looks like a URL, don’t try to resolve locally here.
    if src.startswith(("http://", "https://", "urn:", "biomodels:", "BIOMD")):
        return fallback_sbml_path

    # Local relative reference
    candidate = os.path.abspath(os.path.join(sedml_dir, src))
    if os.path.exists(candidate):
        return candidate

    return fallback_sbml_path


# ----------------------------
# BioModels fetching
# ----------------------------

def fetch_biomodel_files_to_dir(biomodel_file_entry: Any, out_dir: str) -> str:
    """
    Uses biomodels.get_file(entry) which *typically* downloads to a local path.
    But some implementations return bytes or a temp path; we normalize to a file path.
    """
    f = biomodels.get_file(biomodel_file_entry)

    # Common case: it's already a path-like
    if isinstance(f, (str, os.PathLike)) and os.path.exists(str(f)):
        return str(f)

    # If it's bytes-like or a string payload, write it
    name = _file_name(biomodel_file_entry)
    out_path = os.path.join(out_dir, name)

    if isinstance(f, bytes):
        Path(out_path).write_bytes(f)
        return out_path

    # fallback: write string representation
    Path(out_path).write_text(str(f), encoding="utf-8")
    return out_path


def load_biomodel(biomodel_id: str, metadata_or_entry: Any) -> BiomodelLoadResult:
    entry_files = list(_iter_entry_files(metadata_or_entry))

    sedml_entry = find_first_sedml(entry_files)
    sbml_entry = find_first_sbml(entry_files)

    if sedml_entry is None:
        raise ValueError(f"{biomodel_id}: could not find a .sedml file in entry.")
    if sbml_entry is None:
        raise ValueError(f"{biomodel_id}: could not find an SBML (.xml/.sbml) file in entry.")

    with tempfile.TemporaryDirectory(prefix=f"biomodel_{biomodel_id}_") as tmp:
        sedml_path = fetch_biomodel_files_to_dir(sedml_entry, tmp)
        sbml_path = fetch_biomodel_files_to_dir(sbml_entry, tmp)

        sed_doc = read_sedml_doc(sedml_path)
        utc = extract_first_uniform_time_course(sed_doc)

        sedml_dir = os.path.dirname(os.path.abspath(sedml_path))
        resolved_sbml = resolve_sbml_source_from_sedml(sed_doc, sedml_dir, sbml_path)

        # IMPORTANT: tmp dir will be deleted; persist files you need.
        # So we copy them to a stable location next to cwd (or wherever you want).
        stable_dir = os.path.abspath(os.path.join("models", biomodel_id))
        os.makedirs(stable_dir, exist_ok=True)

        stable_sedml = os.path.join(stable_dir, os.path.basename(sedml_path))
        stable_sbml = os.path.join(stable_dir, os.path.basename(resolved_sbml))

        # copy file contents
        Path(stable_sedml).write_bytes(Path(sedml_path).read_bytes())
        Path(stable_sbml).write_bytes(Path(resolved_sbml).read_bytes())

    return BiomodelLoadResult(
        biomodel_id=biomodel_id,
        sbml_path=stable_sbml,
        sedml_path=stable_sedml,
        utc=utc,
    )


# ----------------------------
# Process-bigraph document creation
# ----------------------------

def make_utc_step_state(
    step_name: str,
    step_address: str,
    sbml_path: str,
    utc: UniformTimeCourseSpec,
) -> Dict[str, Any]:
    """
    Creates the state snippet for a UTC step. Adjust ports to match your step’s actual contract.
    """
    return {
        f"{step_name}_step": {
            "_type": "step",
            "address": step_address,
            "config": {
                "model_source": sbml_path,
                # Interpret "time" as end time or duration depending on your step.
                # Here we pass duration based on SED-ML output window:
                "time": float(utc.duration),
                "n_points": int(utc.number_of_points),
                # You might also want:
                # "initial_time": float(utc.initial_time),
                # "output_start_time": float(utc.output_start_time),
            },
            "inputs": {
                "concentrations": ["species_concentrations"],
                "counts": ["species_counts"],
            },
            "outputs": {
                "result": ["results", step_name],
            },
        },
        # optional plot node / other analysis nodes
        "plot": {},
    }


def make_biomodel_document(
    biomodel_id: str,
    sbml_path: str,
    utc: UniformTimeCourseSpec,
    steps: Dict[str, str],
) -> Dict[str, Any]:
    """
    Builds a document with one step per engine, namespaced under the biomodel_id.
    """
    state: Dict[str, Any] = {}

    for engine_name, engine_address in steps.items():
        step_key = f"{biomodel_id}_{engine_name}"
        state.update(
            make_utc_step_state(
                step_name=step_key,
                step_address=engine_address,
                sbml_path=sbml_path,
                utc=utc,
            )
        )

    return {"state": state}


# ----------------------------
# Runner
# ----------------------------

def run_biomodels(core, number_of_models: int = 2) -> List[BiomodelLoadResult]:
    biomodel_ids = biomodels.get_all_identifiers()[:number_of_models]
    biomodel_metadata = {bid: biomodels.get_metadata(bid) for bid in biomodel_ids}

    steps = {
        "copasi": "local:CopasiUTCStep",
        "tellurium": "local:TelluriumUTCStep",
    }

    loaded: List[BiomodelLoadResult] = []

    for biomodel_id in biomodel_ids:
        meta = biomodel_metadata[biomodel_id]
        result = load_biomodel(biomodel_id, meta)
        loaded.append(result)

        doc = make_biomodel_document(
            biomodel_id=biomodel_id,
            sbml_path=result.sbml_path,
            utc=result.utc,
            steps=steps,
        )

        # What you do here depends on how you run process-bigraph docs in your codebase.
        # Examples (pick the one that matches your stack):
        #
        # composite = Composite.from_document(doc, core=core)
        # out = composite.run(...)
        #
        # or:
        # out = run_composite_document(doc, core=core)
        #
        # For now, we just save the doc for inspection:
        out_path = os.path.join("documents", f"{biomodel_id}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        Path(out_path).write_text(__import__("json").dumps(doc, indent=2), encoding="utf-8")

    return loaded


if __name__ == "__main__":
    core = allocate_core()
    loaded = run_biomodels(core, number_of_models=2)
    print(f"Loaded {len(loaded)} biomodel(s).")
