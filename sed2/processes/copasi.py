from typing import Dict, Any
from process_bigraph import Process, Step, Composite, ProcessTypes
from basico import (
    load_model,
    get_species,
    get_reactions,
    set_species,
    run_time_course,
)
import COPASI

def _set_initial_concentrations(changes, dm):
    """
    changes: iterable of (species_name, value) pairs
    dm: COPASI DataModel as returned by basico.load_model
    """
    model = dm.getModel()
    assert isinstance(model, COPASI.CModel)

    references = COPASI.ObjectStdVector()

    for name, value in changes:
        species = model.getMetabolite(name)
        if species is None:
            print(f"Species {name} not found in model")
            continue
        assert isinstance(species, COPASI.CMetab)
        species.setInitialConcentration(float(value))
        references.append(species.getInitialConcentrationReference())

    if len(references) > 0:
        model.updateInitialValues(references)


def _get_transient_concentration(name, dm):
    """
    Return the *current* concentration (not initial) of a species.
    """
    model = dm.getModel()
    assert isinstance(model, COPASI.CModel)

    species = model.getMetabolite(name)
    if species is None:
        print(f"Species {name} not found in model")
        return None
    assert isinstance(species, COPASI.CMetab)
    return float(species.getConcentration())


class CopasiUTCStep(Step):
    """
    ODE component of the dfba hybrid using COPASI (basico + direct COPASI API).
    """

    config_schema = {
        # Path or identifier for the COPASI model (cps / sbml)
        'model_source': 'string',
        # simulation time interval
        'time': 'float',
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        # basico DataModel
        self.dm = load_model(self.config['model_source'])
        # underlying COPASI CModel (used by the speed-up helpers)
        self.cmodel = self.dm.getModel()

        # cache species and reaction names once
        spec_df = get_species(model=self.dm)
        self.species_names = spec_df.index.tolist()

        rxn_df = get_reactions(model=self.dm)
        self.reaction_names = rxn_df.index.tolist()

        self.interval = self.config.get('time', 1.0)

    def initial_state(self) -> Dict[str, Any]:
        species_concentrations = {
            name: _get_transient_concentration(name=name, dm=self.dm)
            for name in self.species_names
        }

        rxn_df = get_reactions(model=self.dm)
        reaction_fluxes = {
            rxn_id: float(rxn_df.loc[rxn_id, 'flux'])
            for rxn_id in self.reaction_names
        }

        return {
            'species_concentrations': species_concentrations,
            # 'reaction_fluxes': reaction_fluxes,
        }

    def inputs(self):
        return {
            'species_concentrations': 'map[float]',
            'species_counts': 'map[float]',
        }

    def outputs(self):
        # Keep nested 'results' for now to match your original API.
        return {
            'results': 'any',
        }

    def update(self, inputs):
        # --- 1) Prepare changes and update initial values efficiently ---

        # You can swap this to inputs['species_concentrations'] if that’s the true source
        spec_data = inputs.get('species_counts', {}) or {}

        # Only include species that actually exist in the model
        changes = [
            (name, float(value))
            for name, value in spec_data.items()
            if name in self.species_names
        ]

        if changes:
            _set_initial_concentrations(changes, self.dm)

        # --- 2) Run COPASI time course ---
        tc = run_time_course(
            start_time=0.0,
            duration=self.interval,
            update_model=True,
            model=self.dm,
        )

        # --- 3) Read back state using the fast helper ---

        species_concentrations = {
            name: _get_transient_concentration(name=name, dm=self.dm)
            for name in self.species_names
        }

        # --- 4) Reaction fluxes  ---

        rxn_df = get_reactions(model=self.dm)
        reaction_fluxes = {
            rxn_id: float(rxn_df.loc[rxn_id, 'flux'])
            for rxn_id in self.reaction_names
        }

        results = {
            'species_concentrations': species_concentrations,
            'reaction_fluxes': reaction_fluxes,
        }

        return {'results': results}


def run_test(core):

    document = {
        'copasi': {
            '_type': 'step',
            'model_source': 'examples/models/biomass_production.cps',
            'time': 10.0,
        }
    }

    sim = Composite(document, core=core)

    
if __name__ == '__main__':
    core = ProcessTypes()
    core.register_process('copasi_utc', CopasiUTCStep)

    run_test(core=core)