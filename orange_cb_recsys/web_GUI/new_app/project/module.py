from abc import ABC, abstractmethod
from enum import Enum


class PossiblePageStatus(Enum):
    INCOMPLETE = 0
    COMPLETE = 1
    DISABLED = 2


class AnalyzerType(Enum):
    ITEMS = 0
    USERS = 1
    RATINGS = 2


class Module(ABC):

    _pages_status = {}
    _algorithms = {}

    def __init__(self):
        self._output_directory = ""
        pass

    @property
    def output_directory(self):
        return self._output_directory

    @output_directory.setter
    def output_directory(self, new_output_directory):
        self._output_directory = new_output_directory

    @property
    def pages_status(self):
        return self._pages_status

    def set_page_status(self, page, new_status):
        if page in self._pages_status:
            self._pages_status[page] = new_status
            result = True
        else:
            result = False
        return result

    def get_page_status(self, page):
        return self._pages_status[page] if page in self._pages_status else None

    def get_module_status(self):
        status = PossiblePageStatus.COMPLETE if \
            all(self.pages_status[page_status] == PossiblePageStatus.COMPLETE for page_status in self.pages_status) else (
                PossiblePageStatus.DISABLED if
                all(self.pages_status[page_status] == PossiblePageStatus.DISABLED for page_status in self.pages_status) else
                PossiblePageStatus.INCOMPLETE)
        return status

    @abstractmethod
    def produce_config_file(self):
        pass

    @abstractmethod
    def is_complete(self):
        pass


class ContentAnalyzerModule(Module):

    def __init__(self, dbpedia_classes):
        super().__init__()
        self._analyzer_type = AnalyzerType.ITEMS
        self._source_path = ""
        self._source_type = ""
        self._dbpedia_classes = dbpedia_classes
        self._exogenous_techniques = []
        self._fields_list = []
        self.__init_pages_status()

    def __init_pages_status(self):
        self._pages_status = {
            "Upload": PossiblePageStatus.DISABLED,
            "Fields": PossiblePageStatus.DISABLED,
            "Algorithms": PossiblePageStatus.DISABLED,
            "Exogenous": PossiblePageStatus.DISABLED
        }

    @property
    def fields_list(self):
        return self._fields_list

    @fields_list.setter
    def fields_list(self, new_fields_list):
        self._fields_list = new_fields_list

    @property
    def dbpedia_classes(self):
        return self.__dbpedia_classes

    @property
    def analyzer_type(self):
        return self.__analyzer_type

    @analyzer_type.setter
    def analyzer_type(self, new_type):
        self._analyzer_type = new_type

    def is_complete(self):
        return self._pages_status["Algorithms"] == PossiblePageStatus.COMPLETE or \
                self._pages_status["Exogenous"] == PossiblePageStatus.COMPLETE

    def has_already_dataset(self):
        return self._pages_status["Upload"] == PossiblePageStatus.COMPLETE

    @staticmethod
    def convert_key(key):
        if "__fieldid" in key:
            return ""
        return key[:key.rindex("__")]

    @property
    def exogenous_techniques(self):
        return self._exogenous_techniques

    def add_exogenous_technique(self, technique_content):
        self._exogenous_techniques.append(technique_content)

    def remove_exogenous_technique(self, technique_index):
        self._exogenous_techniques.pop(technique_index)

    def update_exogenous_technique(self, technique_index, new_technique):
        self._exogenous_techniques[technique_index] = new_technique

    @property
    def exogenous_algorithms(self):
        return self._algorithms["exogenous"]

    @exogenous_algorithms.setter
    def exogenous_algorithms(self, new_exogenous):
        self._algorithms["exogenous"] = new_exogenous

    @property
    def source_path(self):
        return self._source_path

    @source_path.setter
    def source_path(self, new_source_path):
        if new_source_path != "":
            self._source_path = new_source_path.strip()
            self._source_type = new_source_path[new_source_path.rindex(".") + 1:]
        else:
            self._source_path = ""
            self._source_type = ""

    @property
    def source_type(self):
        return self._source_type

    def from_string_to_index(self, field):
        return None if None else self._fields_list.index(field)

    def produce_config_file(self):
        return ""


class UsersContentAnalyzerModule(ContentAnalyzerModule):
    __order_fields = {}

    def __init__(self, ca_algorithms, dbpedia_classes):
        super().__init__(dbpedia_classes)
        self._analyzer_type = AnalyzerType.USERS
        self.__fields_selected = {}
        self.__id_fields_name = []
        self.content_production_algorithms = ca_algorithms["content_production"]
        self.preprocess_algorithms = ca_algorithms["preprocessing"]
        self.memory_interfaces = ca_algorithms["memory_interfaces"]
        self.exogenous_algorithms = ca_algorithms["exogenous"]

    @property
    def fields_selected(self):
        return self.__fields_selected

    @fields_selected.setter
    def fields_selected(self, new_fields):
        self.fields_selected.clear()
        for key, value in new_fields.items():
            self.set_field(key, value)

    def pop_field(self, index):
        self.fields_selected.pop(index)
        self.__order_fields.pop(index)

    def pop_representation(self, field_name, index):
        try:
            self.fields_selected[field_name].pop(index)
        except IndexError:
            print("IndexError")

    def set_field(self, index, new_field):
        if "__" in index:
            self.__order_fields[ContentAnalyzerModule.convert_key(index)] = index[index.rindex("__") + 2:]
            self.__fields_selected[ContentAnalyzerModule.convert_key(index)] = new_field
        else:
            self.__fields_selected[index] = new_field

    def clear_id_fields(self):
        self.__id_fields_name.clear()

    def order_fields(self):
        self.__order_fields = dict(sorted(self.__order_fields.items(), key=lambda x: x[1]))
        self.fields_selected = dict(sorted(self.fields_selected.items(), key=lambda x: self.__order_fields[x[0]]))

    def clear_fields(self):
        self.__order_fields.clear()
        self.fields_selected.clear()

    @property
    def content_production_algorithms(self):
        return self._algorithms['content_production']

    @content_production_algorithms.setter
    def content_production_algorithms(self, new_algorithms):
        self._algorithms["content_production"] = new_algorithms

    @property
    def preprocess_algorithms(self):
        return self._algorithms['preprocessing']

    @preprocess_algorithms.setter
    def preprocess_algorithms(self, new_algorithms):
        self._algorithms["preprocessing"] = new_algorithms

    @property
    def memory_interfaces(self):
        return self._algorithms['memory_interface']

    @memory_interfaces.setter
    def memory_interfaces(self, new_memory_interface):
        self._algorithms["memory_interface"] = new_memory_interface

    @property
    def id_fields_name(self):
        return self.__id_fields_name

    @id_fields_name.setter
    def id_fields_name(self, new_id_fields):
        self.__id_fields_name = new_id_fields

    def produce_config_file(self):
        config_file_obj = {
            "class": "UserAnalyzerConfig",
            "source": self.__get_source_class(),
            "id": self.id_fields_name,
            "output_directory": self.output_directory,
            "field_dict": self.__convert_fields(),
            "exogenous_representation_list": None,
            "export_json": False
        }

        return [{"module": "contentanalyzer", "config": config_file_obj, "fit": {}}]

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
                    if parameter["type"] == "kwargs":
                        for custom_param_name, custom_param_value in parameter["params"].items():
                            class_obj[custom_param_name] = custom_param_value
                    else:
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

    def __convert_memory_interface(self, memory_interfaces):
        memory_interface = {}

        if memory_interfaces["use"]:
            interface = [temp for temp in memory_interfaces["algorithms"] if temp["name"] == memory_interfaces["value"]][0]
            for parameter in interface["params"]:
                memory_interface[parameter["name"]] = self.__convert_class(parameter)
            memory_interface["class"] = interface["name"]
        else:
            return None

        return memory_interface

    def __convert_representations(self, representations):
        converted_representations = []
        for representation in representations:
            temp_mi = self.__convert_memory_interface(representation["memory_interfaces"])

            obj_to_append = {
                "class": "FieldConfig",
                "content_technique": self.__convert_algorithm(representation["algorithm"]),
                "preprocessing": self.__convert_preprocess(representation["preprocess"]),
                "id": representation["id"]
            }

            if temp_mi is not None:
                obj_to_append["memory_interface"] = temp_mi

            converted_representations.append(obj_to_append)
        return converted_representations

    def __convert_fields(self):
        converted_fields = {}
        for name_field, representations in self.__fields_selected.items():
            converted_fields[name_field] = self.__convert_representations(representations)
        return converted_fields

    def __get_source_class(self):
        obj_return = {
            "class": self._source_type + "file",
            "file_path": self._source_path,
        }

        if self._source_type == "csv":
            obj_return["has_header"] = True

        return obj_return


class ItemsContentAnalyzerModule(ContentAnalyzerModule):
    __order_fields = {}

    def __init__(self, ca_algorithms, dbpedia_classes):
        super().__init__(dbpedia_classes)
        self.__analyzer_type = AnalyzerType.ITEMS
        self.__fields_selected = {}
        self.__id_fields_name = []
        self._analyzer_type = AnalyzerType.USERS
        self.__fields_selected = {}
        self.__id_fields_name = []
        self.content_production_algorithms = ca_algorithms["content_production"]
        self.preprocess_algorithms = ca_algorithms["preprocessing"]
        self.memory_interfaces = ca_algorithms["memory_interfaces"]
        self.exogenous_algorithms = ca_algorithms["exogenous"]

    @property
    def fields_selected(self):
        return self.__fields_selected

    @fields_selected.setter
    def fields_selected(self, new_fields):
        self.fields_selected.clear()
        for key, value in new_fields.items():
            self.set_field(key, value)

    def pop_field(self, index):
        self.fields_selected.pop(index)
        self.__order_fields.pop(index)

    def pop_representation(self, field_name, index):
        try:
            self.fields_selected[field_name].pop(index)
        except IndexError:
            print("IndexError")

    def set_field(self, index, new_field):
        if "__" in index:
            self.__order_fields[ContentAnalyzerModule.convert_key(index)] = index[index.rindex("__") + 2:]
            self.__fields_selected[ContentAnalyzerModule.convert_key(index)] = new_field
        else:
            self.__fields_selected[index] = new_field

    def clear_id_fields(self):
        self.__id_fields_name.clear()

    def order_fields(self):
        self.__order_fields = dict(sorted(self.__order_fields.items(), key=lambda x: x[1]))
        self.fields_selected = dict(sorted(self.fields_selected.items(), key=lambda x: self.__order_fields[x[0]]))

    def clear_fields(self):
        self.__order_fields.clear()
        self.fields_selected.clear()

    @property
    def content_production_algorithms(self):
        return self._algorithms['content_production']

    @content_production_algorithms.setter
    def content_production_algorithms(self, new_algorithms):
        self._algorithms["content_production"] = new_algorithms

    @property
    def preprocess_algorithms(self):
        return self._algorithms['preprocessing']

    @preprocess_algorithms.setter
    def preprocess_algorithms(self, new_algorithms):
        self._algorithms["preprocessing"] = new_algorithms

    @property
    def memory_interfaces(self):
        return self._algorithms['memory_interface']

    @memory_interfaces.setter
    def memory_interfaces(self, new_memory_interface):
        self._algorithms["memory_interface"] = new_memory_interface

    @property
    def id_fields_name(self):
        return self.__id_fields_name

    @id_fields_name.setter
    def id_fields_name(self, new_id_fields):
        self.__id_fields_name = new_id_fields

    def produce_config_file(self):
        config_file_obj = {
            "class": "ItemAnalyzerConfig",
            "source": self.__get_source_class(),
            "id": self.id_fields_name,
            "output_directory": self.output_directory,
            "field_dict": self.__convert_fields(),
            "exogenous_representation_list": self.__convert_exogenous_properties(),
            "export_json": False
        }

        return [{"module": "contentanalyzer", "config": config_file_obj, "fit": {}}]

    def __convert_exogenous_property(self, exogenous):
        class_to_convert = exogenous["content"][0]
        to_return = {'class': 'ExogenousConfig'}
        for parameter in class_to_convert["params"]:
            to_add = self.__convert_class(parameter)
            if "class" in to_add and to_add["class"] == "PropertiesFromDataset":
                to_add["field_name_list"] = [field["name"] for field in exogenous["fields_list"]]
            to_return[parameter["name"]] = to_add
        return to_return

    def __convert_exogenous_properties(self):
        return [self.__convert_exogenous_property(exogenous) for exogenous in self.exogenous_techniques]

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
                    if parameter["type"] == "kwargs":
                        for custom_param_name, custom_param_value in parameter["params"].items():
                            class_obj[custom_param_name] = custom_param_value
                    else:
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

    def __convert_memory_interface(self, memory_interfaces):
        memory_interface = {}

        if memory_interfaces["use"]:
            interface = [temp for temp in memory_interfaces["algorithms"] if temp["name"] == memory_interfaces["value"]][0]
            for parameter in interface["params"]:
                memory_interface[parameter["name"]] = self.__convert_class(parameter)
            memory_interface["class"] = interface["name"]
        else:
            return None

        return memory_interface

    def __convert_representations(self, representations):
        converted_representations = []
        for representation in representations:
            temp_mi = self.__convert_memory_interface(representation["memory_interfaces"])

            obj_to_append = {
                "class": "FieldConfig",
                "content_technique": self.__convert_algorithm(representation["algorithm"]),
                "preprocessing": self.__convert_preprocess(representation["preprocess"]),
                "id": representation["id"]
            }

            if temp_mi is not None:
                obj_to_append["memory_interface"] = temp_mi

            converted_representations.append(obj_to_append)
        return converted_representations

    def __convert_fields(self):
        converted_fields = {}
        for name_field, representations in self.__fields_selected.items():
            converted_fields[name_field] = self.__convert_representations(representations)
        return converted_fields

    def __get_source_class(self):
        obj_return = {
            "class": self._source_type + "file",
            "file_path": self._source_path,
        }

        if self._source_type == "csv":
            obj_return["has_header"] = True

        return obj_return


class RecommenderSystemModule(Module):

    def __init__(self, recsys_algorithms):
        super().__init__()
        self.__fields_dict = {}
        self.algorithms = recsys_algorithms
        self.__selected_algorithm = ""
        self.__path_from_ca = {
            "Items": False,
            "Users": False,
            "Ratings": False
        }
        self.__items_path = ""
        self.__users_path = ""
        self.__rating_path = ""
        self.__content = {
            "Fields": {
                "Items": {},
                "Users": {},
                "Ratings": {}
            },
            "Exogenous": {
                "Items": {},
                "Users": {},
                "Ratings": {}
            }
        }
        self.__init_pages_status()

    @property
    def exogenous_techniques(self):
        return self.__content["Exogenous"]

    @exogenous_techniques.setter
    def exogenous_techniques(self, new_techniques):
        self.__content["Exogenous"] = new_techniques

    @property
    def fields_representations(self):
        return self.__content["Fields"]

    @property
    def exogenous_techniques_items(self):
        return self.__content["Exogenous"]["Items"]

    @exogenous_techniques_items.setter
    def exogenous_techniques_items(self, new_techniques):
        self.__content["Exogenous"]["Items"] = new_techniques

    @property
    def fields_representations_items(self):
        return self.__content["Fields"]["Items"]

    @fields_representations_items.setter
    def fields_representations_items(self, new_fields):
        self.__content["Fields"]["Items"] = new_fields

    @property
    def exogenous_techniques_users(self):
        return self.__content["Exogenous"]["Users"]

    @exogenous_techniques_users.setter
    def exogenous_techniques_users(self, new_techniques):
        self.__content["Exogenous"]["Users"] = new_techniques

    @property
    def fields_representations_users(self):
        return self.__content["Fields"]["Users"]

    @fields_representations_users.setter
    def fields_representations_users(self, new_fields):
        self.__content["Fields"]["Users"] = new_fields

    def __init_pages_status(self):
        self._pages_status = {
            "Upload": PossiblePageStatus.DISABLED,
            "Representations": PossiblePageStatus.DISABLED,
        }

    def is_path_items_from_ca(self):
        return self.__path_from_ca["Items"]

    def is_path_users_from_ca(self):
        return self.__path_from_ca["Users"]

    def is_path_ratings_from_ca(self):
        return self.__path_from_ca["Ratings"]

    def set_path_from_ca(self, path_type, is_from_ca):
        self.__path_from_ca[path_type] = is_from_ca

    @property
    def items_path(self):
        return self.__items_path

    @items_path.setter
    def items_path(self, new_items_path):
        self.__items_path = new_items_path

    @property
    def users_path(self):
        return self.__users_path

    @users_path.setter
    def users_path(self, new_users_path):
        self.__users_path = new_users_path

    @property
    def ratings_path(self):
        return self.__ratings_path

    @ratings_path.setter
    def ratings_path(self, new_ratings_path):
        self.__rating_path = new_ratings_path

    @property
    def field_dict(self):
        return self.__fields_dict

    @field_dict.setter
    def field_dict(self, new_field_dict):
        # TODO: Check if fields (and representations) in new_field_dict are present in __content
        self.__fields_dict = new_field_dict

    @property
    def selected_algorithm(self):
        return self.__selected_algorithm

    @selected_algorithm.setter
    def selected_algorithm(self, new_algorithm):
        # TODO: Check if new_algorithm is in __algorithms
        self.__selected_algorithm = new_algorithm

    def is_complete(self):
        return self._pages_status["Representations"] == PossiblePageStatus.COMPLETE

    def produce_config_file(self):
        return ""

    @property
    def content(self):
        return self.__content

    @content.setter
    def content(self, new_content):
        self.__content = new_content

    def append_representation_field(self, field_name, id_representation):
        if field_name in self.__fields_dict:
            self.__fields_dict[field_name].append(id_representation)
        else:
            self.__fields_dict[field_name] = [id_representation]


class RatingsContentAnalyzerModule(ContentAnalyzerModule):
    def __init__(self, ca_algorithms, dbpedia_classes):
        super().__init__(dbpedia_classes)
        self.ratings_algorithms = ca_algorithms["ratings"]
        self.__analyzer_type = AnalyzerType.RATINGS
        self.__ratings_properties = {
            "from_id": 0,
            "to_id": 1,
            "score": 2,
            "timestamp": 3
        }

    @property
    def ratings_properties(self):
        return self.__ratings_properties

    @property
    def from_id_column(self):
        return self.__ratings_properties["from_id"]

    @from_id_column.setter
    def from_id_column(self, new_id):
        self.__ratings_properties["from_id"] = \
            new_id if type(new_id).__name__ == "int" else self.from_string_to_index(new_id)

    @property
    def to_id_column(self):
        return self.__ratings_properties["to_id"]

    @to_id_column.setter
    def to_id_column(self, new_id):
        self.__ratings_properties["to_id"] = \
            new_id if type(new_id).__name__ == "int" else self.from_string_to_index(new_id)

    @property
    def score_column(self):
        return self.__ratings_properties["score"]

    @score_column.setter
    def score_column(self, new_id):
        self.__ratings_properties["score"] = \
            new_id if type(new_id).__name__ == "int" else self.from_string_to_index(new_id)

    @property
    def timestamp_column(self):
        return self.__ratings_properties["timestamp"]

    @timestamp_column.setter
    def timestamp_column(self, new_id):
        self.__ratings_properties["timestamp"] = \
            new_id if type(new_id).__name__ == "int" else self.from_string_to_index(new_id)

    @property
    def ratings_algorithms(self):
        return self._algorithms["ratings"]

    @ratings_algorithms.setter
    def ratings_algorithms(self, new_ratings):
        self._algorithms["ratings"] = new_ratings

    def produce_config_file(self):
        return ""

