from process_bigraph import ProcessTypes
from bigraph_viz import VisualizeTypes
from sed2.processes.copasi_process import CopasiUTCStep, CopasiUTCProcess, CopasiSteadyStateStep
from sed2.processes.tellurium_process import TelluriumUTCStep, TelluriumSteadyStateStep
from sed2.processes.comparison_processes import CompareResults


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

class VivariumTypes(ProcessTypes, VisualizeTypes):
    def __init__(self):
        super().__init__()

def get_sed_core():
    core = VivariumTypes()
    return register_processes(core)
