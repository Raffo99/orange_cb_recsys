from orange_cb_recsys.content_analyzer.field_content_production_techniques.field_content_production_technique \
    import FieldContentProductionTechnique
from orange_cb_recsys.content_analyzer.information_processor.information_processor import InformationProcessor
from inspect import signature

import orange_cb_recsys.utils.runnable_instances as r_i
import typing


def get_ca_algorithms():
    """
    Method used to get all the implemented content analyzer algorithms and their parameters
    Returns:
        Three different lists of algorithms for content production, preprocessing and memory interface with this typo:
            [
                {
                    'name': 'Algorithm Name',
                    'params': [
                        {'name': 'Parameter', 'type': 'str'},
                        {'name': 'Union Parameter', type: 'Union', 'params': [...]},
                        {...}
                    ]
                }, {...}
            ]
    """
    content_production_algorithms = []
    preprocessing_algorithms = []
    memory_interfaces = []

    # Get all classes implemented for content_production
    content_production_classes = r_i.get_all_implemented_classes(FieldContentProductionTechnique)
    # Get all classes implemented for preprocessing
    preprocessing_classes = r_i.get_all_implemented_classes(InformationProcessor)
    # Get all classes implemented fro memory interface

    add_algorithms(content_production_algorithms, content_production_classes)
    content_production_algorithms.sort(key=lambda x: x['name'])
    add_algorithms(preprocessing_algorithms, preprocessing_classes)

    return content_production_algorithms, preprocessing_algorithms, memory_interfaces


def add_algorithms(algorithms_array, classes_array):
    """
    Support method for get_ca_algorithms, it takes an algorithm array and for each algorithm retrieves all his
    parameters, to then append them to the classes_array

    Args:
        algorithms_array: array with the algorithms to append to classes_array
        classes_array: array to append the algorithms in algorithms_array with all their parameters
    """
    for algorithm_class in classes_array:
        signature_parameters = list(signature(algorithm_class).parameters.items())

        # Get all the parameter of the instance
        parameters_array = get_parameters(signature_parameters)

        algorithms_array.append({
            'name': algorithm_class.__name__,
            'params': parameters_array
        })


def get_parameters(signature_parameters):
    """
    Support method for add_algorithms, it takes the parameters for an algorithm and return an extensive representation
    of the parameters, it go deeper in the possible values of the parameters and call itself if the parameters
    is a complex class (ex. simple class: 'str', 'bool', 'int', 'float', ...)
    Args:
        signature_parameters: signature parameters of the algorithm
    Returns:
        List of parameters with the type, other parameters if a complex class, etc. with this typo
        [
            {'name': 'Parameter', 'type': 'str'},
            {'name': 'Union Parameter', type: 'Union', 'params': [...]},
            {...}
        ]
    """
    if "self" in signature_parameters:
        signature_parameters.remove("self")

    parm_list = []

    for parm in signature_parameters:
        if hasattr(parm[1].annotation, '__origin__'):
            if parm[1].annotation.__origin__ is typing.Union:
                temp_parameters = []
                for arg in parm[1].annotation.__args__:
                    try:
                        temp_parameters.append({
                            'name': arg.__name__,
                            'type': arg.__name__,
                            'params': get_parameters(list((signature(arg).parameters.items())))
                        })
                    except ValueError:
                        temp_parameters.append({
                            'name': arg.__name__ if arg.__name__ != "str" else "String",
                            'type': arg.__name__,
                            'params': [{
                                'name': arg.__name__,
                                'type': arg.__name__
                            }]
                        })

                parm_list.append({
                    'name': parm[1].name,
                    'type': 'Union',
                    'params': temp_parameters
                })
        elif hasattr(parm[1].annotation, "__name__"):
            parm_class = parm[1].annotation.__name__
            try:
                if parm[1].name == "lang" or parm[1].name == "kwargs":
                    continue

                sub_classes = r_i.get_all_implemented_classes(parm[1].annotation)
                temp_parameters = []
                for sub_class in sub_classes:
                    temp_parameters.append({
                        'name': sub_class.__name__,
                        'params': get_parameters(list((signature(sub_class).parameters.items())))
                    })

                parm_list.append({
                    'name': parm[1].name,
                    'type': "Union",
                    'params': temp_parameters
                })
            except ValueError:
                parm_list.append({
                    'name': parm[1].name,
                    'type': parm_class
                })
    return parm_list
