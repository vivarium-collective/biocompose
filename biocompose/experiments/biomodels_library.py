from process_bigraph import allocate_core, Composite

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

# def find_sbml(entry):
#     return entry[0]  # hack assumes sbml is first file in entry

import os
import tellurium as te

def load_biomodel(entry):
    sbml_entry = entry[0]
    sedml_entry = find_sedml(entry)
    # sbml_file = find_sbml(entry)

    sedml_file = biomodels.get_file(sedml_entry)
    sbml_file = biomodels.get_file(sbml_entry)
    sed_ml_str = str(sedml_file)
    sed_doc = libsedml.readSedMLFromFile(sed_ml_str)

    # loop through tasks, look for uniform time course, get simulation time and save points.





    results = te.executeSEDML(sed_doc.toSed(),
                              workingDir=os.path.dirname(sed_ml_str),
                              )

    breakpoint()

    # return sbml, total_time, time_steps



def run_biomodels(core):
    number_of_models = 2
    biomodel_ids = biomodels.get_all_identifiers()[:number_of_models]
    biomodel_metadata = get_metadata(biomodel_ids)

    biomodel_models = {
        biomodel_id: load_biomodel(metadata)
        for biomodel_id, metadata in biomodel_metadata.items()
    }


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
                        'model_source': 'models/BIOMD0000000012_url.xml',  # replace this with the retrieved sbml
                        'time': 10,                     # replace with
                        'n_points': 10,
                    },
                    'inputs': {
                        'concentrations': ['species_concentrations'],
                        'counts': ['species_counts']},
                    'outputs': {
                        'result': ['results', step_name],
                    },
                },
                'plot': {}
            }

            # export results as CSV for comparison with SED-ML results.

    

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
    core = allocate_core()
    run_biomodels(core)

    print('biomodels')
