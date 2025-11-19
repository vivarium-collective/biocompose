from process_bigraph import ProcessTypes
from biocompose.processes.copasi_process import CopasiUTCStep, CopasiUTCProcess, CopasiSteadyStateStep
from biocompose.processes.tellurium_process import TelluriumUTCStep, TelluriumSteadyStateStep
from biocompose.processes.comparison_processes import CompareResults


PROCESS_DICT = {
    "CopasiUTCProcess": CopasiUTCProcess,
    "CopasiUTCStep": CopasiUTCStep,
    "CopasiSteadyStateStep": CopasiSteadyStateStep,
    "TelluriumUTCStep": TelluriumUTCStep,
    "TelluriumSteadyStateStep": TelluriumSteadyStateStep,
    "CompareResults": CompareResults,
}


def register_processes(core):
    for process_name, process in PROCESS_DICT.items():
        core.register_process(process_name, process)
    return core


def get_sed_core():
    core = ProcessTypes()
    return register_processes(core)
