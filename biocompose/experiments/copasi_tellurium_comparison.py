'''
Experiment comparing simulation results from Copasi and Tellurium
'''
from biocompose import create_core
from process_bigraph import Composite

def run_comparison_experiment(core):
    doc = {
        # provide initial values to overwrite those in the configured model
        'species_concentrations': {},
        'species_counts': {},

        'tellurium_step': {
            '_type': 'step',
            'address': 'local:TelluriumUTCStep',
            'config': {
                'model_source': 'models/BIOMD0000000012_url.xml',
                'time': 10,
                'n_points': 10,
            },
            'inputs': {
                'concentrations': ['species_concentrations'],
                'counts': ['species_counts']},
            'outputs': {
                'result': ['results', 'tellurium'],
            },
        },

        'copasi_step': {
            '_type': 'step',
            'address': 'local:CopasiUTCStep',
            'config': {
                'model_source': 'models/BIOMD0000000012_url.xml',
                'time': 10,
                'n_points': 10,
            },
            'inputs': {
                'concentrations': ['species_concentrations'],
                'counts': ['species_counts']},
            'outputs': {
                'result': ['results', 'copasi'],
            },
        },

        'comparison': {
            '_type': 'step',
            'address': 'local:CompareResults',
            'config': {},
            'inputs': {
                'results': ['results'],
            },
            'outputs': {
                'comparison': ['comparison_result'],
            },
        },
    }

    doc = {'state': doc}
    sim = Composite(doc, core=core)
    sim.run(0)

    print(
        sim.state['comparison_result'])



if __name__ == '__main__':
    core = create_core()
    run_comparison_experiment(core)
