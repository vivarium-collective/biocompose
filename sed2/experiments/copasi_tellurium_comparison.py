'''
Experiment comparing simulation results from Copasi and Tellurium
'''
from sed2 import create_core
from process_bigraph import Composite
from bigraph_viz import plot_bigraph


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
                'species_concentrations': ['species_concentrations'],
                'species_counts': ['species_counts']},
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
                'species_concentrations': ['species_concentrations'],
                'species_counts': ['species_counts']},
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

    plot_settings = {}
    plot_settings.update(dict(
        dpi='300',
        show_values=True,
        show_types=True,
        # collapse_redundant_processes={},
        value_char_limit=20,
        type_char_limit=40,
    ))
    plot_bigraph(
        state=sim.state,
        schema=sim.composition,
        core=core,
        out_dir='out',
        filename=f"sed_comparison_bigraph_before",
        **plot_settings
    )

    sim.run(0)

    print(
        sim.state['comparison_result'])

    plot_bigraph(
        state=sim.state,
        schema=sim.composition,
        core=core,
        out_dir='out',
        filename=f"sed_comparison_bigraph_after",
        **plot_settings)

if __name__ == '__main__':
    core = create_core()
    # core = register_types(core)
    run_comparison_experiment(core)
