from abc import ABC, abstractmethod
from enum import Enum


class PossiblePageStatus(Enum):
    INCOMPLETE = 0
    COMPLETE = 1
    DISABLED = 2
    ENABLED = 3


class Module(ABC):

    _pages_status = {}
    _output_directory = ""
    _algorithms = {}

    def __init__(self):
        pass

    def set_output_directory(self, new_output_directory):
        self._output_directory = new_output_directory

    def get_output_directory(self):
        return self._output_directory

    def get_pages_status(self):
        return self._pages_status

    def set_page_status(self, page, new_status):
        if page in self._pages_status:
            self._pages_status[page] = new_status
            result = True
        else:
            result = False
        return result

    @abstractmethod
    def produce_config_file(self):
        pass

    @abstractmethod
    def is_complete(self):
        pass


class ContentAnalyzerModule(Module):

    __fields = {}
    __content_type = ""
    __source_path = ""
    __source_type = ""
    __id_field_name = []
    __order_fields = {}

    def __init__(self):
        super().__init__()
        self.__init_pages_status()

    def __init_pages_status(self):
        self._pages_status = {
            "Upload": PossiblePageStatus.INCOMPLETE,
            "Fields": PossiblePageStatus.DISABLED,
            "Algorithms": PossiblePageStatus.DISABLED,
            "Execute": PossiblePageStatus.DISABLED
        }

    def is_complete(self):
        return self._pages_status["Algorithms"] == PossiblePageStatus.COMPLETE

    def clear_id_fields(self):
        self.__id_field_name.clear()

    def add_id_field(self, new_field):
        self.__id_field_name.append(new_field)

    def set_fields(self, new_fields):
        self.__fields.clear()
        for key, value in new_fields.items():
            self.set_field(key, value)

    @staticmethod
    def convert_key(key):
        if "__fieldid" in key:
            return ""
        return key[:key.rindex("__")]

    def get_fields(self):
        return self.__fields

    def pop_field(self, index):
        self.__fields.pop(index)
        self.__order_fields.pop(index)

    def pop_representation(self, field_name, index):
        self.__fields[field_name].pop(index)

    def set_field(self, index, new_field):
        if "__" in index:
            self.__order_fields[ContentAnalyzerModule.convert_key(index)] = index[index.rindex("__") + 2:]
            self.__fields[ContentAnalyzerModule.convert_key(index)] = new_field
        else:
            self.__fields[index] = new_field

    def order_fields(self):
        self.__order_fields = dict(sorted(self.__order_fields.items(), key=lambda x: x[1]))
        self.__fields = dict(sorted(self.__fields.items(), key=lambda x: self.__order_fields[x[0]]))

    def clear_fields(self):
        self.__order_fields.clear()
        self.__fields.clear()

    def get_content_production_algorithms(self):
        return self._algorithms['content_production']

    def set_content_production_algorithms(self, new_algorithms):
        self._algorithms["content_production"] = new_algorithms

    def get_preprocess_algorithms(self):
        return self._algorithms['preprocessing']

    def set_preprocess_algorithms(self, new_algorithms):
        self._algorithms["preprocessing"] = new_algorithms

    def get_memory_interfaces(self):
        return self._algorithms['memory_interface']

    def set_memory_interfaces(self, new_memory_interface):
        self._algorithms["memory_interface"] = new_memory_interface

    def get_source_path(self):
        return self.__source_path

    def set_source_path(self, new_source_path):
        self.__source_path = new_source_path
        self.__source_type = new_source_path[new_source_path.rindex(".") + 1:]

    def __convert_class(self, class_to_convert):
        class_obj = {}
        if "type" not in class_to_convert:
            return class_to_convert["name"]

        if class_to_convert["type"] == "Union":
            parameter_value = list(filter(lambda par: par["name"] == class_to_convert["value"],
                                          class_to_convert["params"]))[0]
            class_obj = self.__convert_class(parameter_value)
        elif class_to_convert["type"] == "Complex":
            if "sub_classes" in class_to_convert:
                parameter_value = list(filter(lambda sub_class: sub_class["name"] == class_to_convert["value"],
                                              class_to_convert["sub_classes"]))[0]
                class_obj = self.__convert_class(parameter_value)
            elif "params" in class_to_convert:
                class_obj = {"class": class_to_convert["name"]}
                for parameter in class_to_convert["params"]:
                    class_obj[parameter["name"]] = self.__convert_class(parameter)
        else:
            return class_to_convert["value"]

        return class_obj

    def __convert_algorithm(self, algorithm):
        algorithm_obj = {"class": algorithm["name"]}
        for parameter in algorithm["params"]:
            algorithm_obj[parameter["name"]] = self.__convert_class(parameter)
        return algorithm_obj

    def __convert_preprocess(self, preprocess_techniques):
        preprocess_list = []
        for preprocess_technique in preprocess_techniques:
            if preprocess_technique["use"]:
                technique = {"class": preprocess_technique["name"]}
                for parameter in preprocess_technique["params"]:
                    technique[parameter["name"]] = self.__convert_class(parameter)
                preprocess_list.append(technique)
        return preprocess_list

    def __convert_representations(self, representations):
        converted_representations = []
        for representation in representations:
            converted_representations.append({
                "class": "FieldConfig",
                "content_technique": self.__convert_algorithm(representation["algorithm"]),
                "preprocessing": self.__convert_preprocess(representation["preprocess"]),
                "id": representation["id"]
            })
        return converted_representations

    def __convert_fields(self):
        converted_fields = []
        for name_field, representations in self.__fields.items():
            converted_fields.append({
                name_field: self.__convert_representations(representations)
            })
        return converted_fields

    def produce_config_file(self):
        config_file_obj = {
            "content_type": self.__content_type,
            "output_directory": self.get_output_directory(),
            "raw_source_path": self.__source_path,
            "source_type": self.__source_type,
            "id_field_name": self.__id_field_name,
            "field_dict": self.__convert_fields()
        }

        return [config_file_obj]


class RecommenderSystemModule(Module):
    def __init__(self):
        super().__init__()
        self.__init_pages_status()

    def __init_pages_status(self):
        self._pages_status = {
            "Upload": PossiblePageStatus.INCOMPLETE,
            "Representations": PossiblePageStatus.DISABLED,
            "Execute": PossiblePageStatus.DISABLED
        }

    def is_complete(self):
        return self._pages_status["Representations"] == PossiblePageStatus.COMPLETE

    def produce_config_file(self):
        return ""
