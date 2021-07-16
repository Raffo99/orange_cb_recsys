import inspect

from orange_cb_recsys.content_analyzer.field_content_production_techniques.field_content_production_technique \
    import FieldContentProductionTechnique
from orange_cb_recsys.content_analyzer.information_processor.information_processor import InformationProcessor
from orange_cb_recsys.recsys.recsys import RecSys
from inspect import signature

import orange_cb_recsys.utils.runnable_instances as r_i
import typing


def get_recsys_algorithms():
    rec_sys = []
    add_algorithms(rec_sys, r_i.get_all_implemented_classes(RecSys))
    return rec_sys


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


def add_algorithms(algorithms_list, classes_list):
    """
    Support method that add all the algorithms in the algorithms_list to the classes_list, with all the parameters for
    every algorithm, and the possible derived classes

    Args:
        algorithms_list: list with the algorithms to append to classes_list
        classes_list: list to append the algorithms in algorithms_list with all their parameters
    """

    # Iterate over every algorithm class and get all parameters with the recursive method
    for algorithm_class in classes_list:
        try:
            # Get all the parameter of the instance
            signature_parameters = list(signature(algorithm_class).parameters.items())

            # If self is in the signature parameters, the method has to remove it
            if "self" in signature_parameters:
                signature_parameters.remove("self")
            parm_list = []

            # Iterate over every parameter in the signature of the class, and use the recursive method on it
            for parm in signature_parameters:
                class_to_append = get_class_with_parameters(parm[1].annotation, parm[0])
                if 'name' in class_to_append:
                    parm_list.append(class_to_append)

            # Create the algorithm object with name and parameters, then append to the list of algorithms
            algorithms_list.append({
                'name': algorithm_class.__name__,
                'params': parm_list
            })

        except ValueError:
            # If there is a problem in the signature function, the class of the algorithm doesn't have parameters
            algorithms_list.append({'name': algorithm_class.__name__})


def get_class_with_parameters(_class, _class_name):
    """
    Recursive method that support the add_algorithms method, it takes in input a class and return an object of
    the class like  this typo:

    {
        'name': 'obj',
        'type': 'str'
    }

    {
        'name': 'obj',
        'type': 'Complex',
        'sub_classes': [{...}]
    }
    ...

    Args:
        _class: class to retrieve the parameters and to create the object to return
        _class_name: name of the parameter that use this class
    """
    simple_classes = ['str', 'float', 'int', 'bool']

    # If the class is a list, the method has to specify it
    if hasattr(_class, "__origin__") and _class.__origin__ is list:
        # TODO: Let the list be a list, not a single item
        _class = _class.__args__[0]

    # If the class is a Union of class, the method has to iterate the method over every class of the Union
    if hasattr(_class, "__origin__") and _class.__origin__ is typing.Union:
        possible_classes = []

        # Iterate over every class in the Union and add it to the list, using recursively this method
        for possible_class in _class.__args__:
            sub_class_name = possible_class.__name__
            class_to_append = get_class_with_parameters(possible_class, sub_class_name)
            if class_to_append.__name__ != 'NoneType' and 'name' in class_to_append:
                possible_classes.append(class_to_append)

        # In the end the method can build the return class object with name, type and parameters list
        return_class = {
            'name': _class_name,
            'type': 'Union',
            'params': possible_classes
        }
    else:
        # TODO: Remove this, i use this for debug the recsys module (problems with the recurion of this method)
        if type(_class).__name__ == "str":
            return

        # If the class is a simple class (ex. string, int, float, etc) the method can simple build the return class object
        try:
            if _class.__name__ in simple_classes:
                return_class = {
                    'name': _class_name,
                    'type': _class.__name__
                }
            else:
                # Either way, if the class is a complex class, the method checks if the class is an abstract class
                if inspect.isabstract(_class):
                    # If the class is an abstract class the method have to iterate over all the derived classes
                    sub_classes = []
                    for sub_class in r_i.get_all_implemented_classes(_class):
                        if sub_class.__name__ == _class_name:
                            continue
                        sub_class_name = sub_class.__name__
                        class_to_append = get_class_with_parameters(sub_class, sub_class_name)
                        if class_to_append.__name__ != 'NoneType' and 'name' in class_to_append:
                            sub_classes.append(class_to_append)

                    # Then the method can build the return class
                    return_class = {
                        'name': _class_name,
                        'type': 'Complex',
                        'sub_classes': sub_classes
                    }
                else:
                    # Otherwise, the method has to iterate the current method
                    # for every parameter in the signature of the class
                    if _class.__name__ == "dict":
                        # TODO: Support dictionary
                        return_class = {'name': 'dict'}
                    else:
                        if _class_name == "kwargs" or _class_name == "lang":
                            return {}
                        class_parameters = []
                        for class_param in list(signature(_class).parameters.items()):
                            class_to_append = get_class_with_parameters(class_param[1].annotation, class_param[0])
                            if class_to_append.__name__ != 'NoneType' and 'name' in class_to_append:
                                class_parameters.append(class_to_append)

                        # Then the method can build the return class
                        return_class = {
                            'name': _class_name,
                            'type': 'Complex',
                            'params': class_parameters
                        }
        except AttributeError:
            # TODO: Support more classes
            print("Attribute error")
            return_class = {}
    return return_class

