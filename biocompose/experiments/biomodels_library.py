from process_bigraph import generate_core, Composite

import biomodels
import libsedml


def get_metadata(biomodel_ids):
    return {
        biomodel_id: biomodels.get_metadata(biomodel_id)
        for biomodel_id in biomodel_ids
    }


def find_sedml(entry):
    for line in entry:
        if line.name.endswith('.sedml'):
            return line


def load_biomodel(entry):
    sbml = entry[0]
    sedml_entry = find_sedml(entry)

    sedml_file = biomodels.get_file(sedml_entry)

    libsedml.read_SedML(sedml_file)

    # TODO: 
    #   * load/read sedml
    #   * find total_time, time_steps

    # total_time = ????
    # time_steps = ????

    # return sbml, total_time, time_steps

    import ipdb; ipdb.set_trace()


def run_biomodels(core):
    biomodel_ids = biomodels.get_all_identifiers()[:10]
    biomodel_metadata = get_metadata(biomodel_ids)

    biomodel_models = {
        biomodel_id: load_biomodel(metadata)
        for biomodel_id, metadata in biomodel_metadata.items()
    }

    import ipdb; ipdb.set_trace()

    steps = {
        'copasi': 'local:CopasiUTCStep',
        'tellurium': 'local:TelluriumUTCStep',
    }

    for step_name, step_address in steps.items():
        for biomodel_id in biomodel_ids:
            biomodel_path

            state = {
                f'{biomodel_id}_{step_name}_step': {
                    '_type': 'step',
                    'address': step_address,
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
                }
            }

    

    # state = {
    #     'tellurium_step': {
    #         '_type': 'step',
    #         'address': 'local:TelluriumUTCStep',
    #         'config': {
    #             'model_source': 'models/BIOMD0000000012_url.xml',
    #             'time': 10,
    #             'n_points': 10,
    #         },
    #         'inputs': {
    #             'concentrations': ['species_concentrations'],
    #             'counts': ['species_counts']},
    #         'outputs': {
    #             'result': ['results', 'tellurium'],
    #         },
    #     },

    #     'copasi_step': {
    #         '_type': 'step',
    #         'address': 'local:CopasiUTCStep',
    #         'config': {
    #             'model_source': 'models/BIOMD0000000012_url.xml',
    #             'time': 10,
    #             'n_points': 10,
    #         },
    #         'inputs': {
    #             'concentrations': ['species_concentrations'],
    #             'counts': ['species_counts']},
    #         'outputs': {
    #             'result': ['results', 'copasi'],
    #         },
    #     },
    
    

if __name__ == '__main__':
    core = generate_core()
    run_biomodels(core)

    print('biomodels')
