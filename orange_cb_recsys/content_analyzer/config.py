import abc
import re
from abc import ABC
from typing import List, Dict, Union, Iterator

from orange_cb_recsys.content_analyzer.field_content_production_techniques.field_content_production_technique import \
    FieldContentProductionTechnique, DefaultTechnique
from orange_cb_recsys.content_analyzer.information_processor.information_processor import InformationProcessor
from orange_cb_recsys.content_analyzer.exogenous_properties_retrieval import ExogenousPropertiesRetrieval
from orange_cb_recsys.content_analyzer.memory_interfaces.memory_interfaces import InformationInterface
from orange_cb_recsys.content_analyzer.raw_information_source import RawInformationSource


class FieldConfig:
    """
    Class that represents the configuration for a single representation of a field. The configuration of a single
    representation is defined by a FieldContentProductionTechnique that will be applied to the pre-processed data
    of said field (EmbeddingTechnique, for example), a list of InformationProcessor that will pre-process the data
    in the field (NLTK, for example), an id which can be used by the user to refer to a particular representation
    (by doing so the user can freely refer to a representation for a field of a content by using the id).
    There is also a memory_interface attribute which allows to define a data structure where the contents can be
    serialized. If None, the output of the field content production technique in the config will be serialized in the
    content itself, otherwise it will be serialized in a InformationInterface.
    If preprocessing is not defined, no preprocessing operations will be done on the field data.
    If id is not defined, a default id will be assigned to the field representation related to this config once it is
    being processed by the ContentAnalyzer.
    Various configurations are possible depending on the type of field the user wants to create.

    EXAMPLE:
        FieldConfig(SkLearnTfIdf(), NLTK(), id='field_example')

        this will produce a field representation using the SkLearnTfIdf technique on the field data,
        preprocessed by NLTK, and the name of the produced representation will be 'field_example'

        FieldConfig(SkLearnTfIdf(), NLTK())

        this will produce the same result as above but the id for the field representation defined by this config will
        be set by the ContentAnalyzer once it is being processed

        FieldConfig(SkLearnTfIdf(), memory_interface=SearchIndex(/somedir))

        this will produce a field representation using the SkLearnTfIdf technique on the field data, but it will not be
        directly stored in the content, instead it will be stored in a index

        FieldConfig(SkLearnTfIdf())

        this time no preprocessing operations will be applied to the field data, only the complex representation will
        be applied

        FieldConfig()

        nothing will be done on the field. The ContentAnalyzer will just decode the data without applying anything else

    Args:
        content_technique (FieldContentProductionTechnique): technique that will be applied to the field in order to
            produce a complex representation of said field
        preprocessing (Union[InformationProcessor, List[InformationProcessor]): list (or single value) of
            InformationProcessor that will be used to modify the data in the field that will be used
            by the content_technique
        memory_interface (InformationInterface): complex structure where the contents can be serialized (an Index for
            example)
        id (str): id to store for the config, this can be used later by the user to refer to the representation
            generated by this config. (the content analyzer main will handle cases where a list of FieldConfigs for a
            field has non unique ids)
        lang (str): string code that represents the language the preprocessors will be set to
    """

    def __init__(self,
                 content_technique: FieldContentProductionTechnique = DefaultTechnique(),
                 preprocessing: Union[InformationProcessor, List[InformationProcessor]] = None,
                 memory_interface: InformationInterface = None,
                 id: str = None,
                 lang: str = "EN"):

        if preprocessing is None:
            preprocessing = []

        if id is not None:
            self._check_custom_id(id)

        self.__content_technique = content_technique
        self.__preprocessing = preprocessing
        self.__memory_interface = memory_interface
        self.__id = id
        self.__lang = lang
        self.__content_technique.lang = self.__lang

        if not isinstance(self.__preprocessing, list):
            self.__preprocessing = [self.__preprocessing]

        for preprocessor in self.__preprocessing:
            preprocessor.lang = self.__lang

    @property
    def memory_interface(self):
        """
        Getter for the index associated to the field config
        """
        return self.__memory_interface

    @property
    def content_technique(self):
        """
        Getter for the field content production technique of the field
        """
        return self.__content_technique

    @property
    def preprocessing(self):
        """
        Getter for the list of preprocessor of the field config
        """
        return self.__preprocessing

    @property
    def id(self):
        """
        Getter for the id of the field config
        """
        return self.__id

    @property
    def lang(self):
        """
        Getter for the language of the field config
        """
        return self.__lang

    def _check_custom_id(self, id: str):
        if not re.match("^[A-Za-z0-9_-]+$", id):
            raise ValueError("The custom id {} is not valid!\n"
                             "A custom id can only have numbers, letters and '_' or '-'!".format(id))

    def __str__(self):
        return "FieldConfig"

    def __repr__(self):
        return "< " + "FieldConfig: " + "" \
               "\nId:" + str(self.__id) + \
               "\nProduction Technique:" + str(self.__content_technique) +\
               "\nInformation Processors: " + str(self.__preprocessing) + " >"


class ExogenousConfig:
    """
    Class that represents the configuration for a single exogenous representation. The config allows the user to
    specify an exogenous properties retrieval technique to use (that will be used to retrieve the data that will
    be stored in the content exogenous dictionary) and an id for the configuration (that can be used by the user
    to refer to the representation that the config will generate).
    It's possible to avoid assigning an id to the Config, in that case the content_analyzer_main will just
    automatically assign a default id to the exogenous representation the config will generate (default ids are
    '0', '1', and so on).

    EXAMPLE:
        ExogenousConfig(DBPediaMappingTechnique('Film', 'EN', 'Title'), 'test')

        will create an exogenous_representation for the content bu retrieving the data regarding it from DBPedia,
        said representation will be named 'test' in the content's exogenous dictionary

        ExogenousConfig(DBPediaMappingTechnique('Film', 'EN', 'Title'))

        same as the example above, but, once in the content analyzer main, the representation generated by the
        exogenous technique will be assigned a default name

    Args:
        exogenous_technique (ExogenousPropertiesRetrieval): technique to use in order to retrieve exogenous data
            regarding the content to store inside of it. An example would be the DBPediaMappingTechnique which allows
            to retrieve properties from DBPedia regarding the item.
        id (str): id to store for the config, this can be used later by the user to refer to the representation
            generated by this config. (the content_analyzer_main will handle cases where a list of ExogenousConfigs
            has non unique ids)
    """

    def __init__(self, exogenous_technique: ExogenousPropertiesRetrieval, id: str = None):
        if id is not None:
            self._check_custom_id(id)

        self.__exogenous_technique = exogenous_technique
        self.__id = id

    @property
    def exogenous_technique(self):
        """
        Getter for the exogenous properties retrieval technique
        """
        return self.__exogenous_technique

    @property
    def id(self):
        """
        Getter for the ExogenousConfig id
        """
        return self.__id

    def _check_custom_id(self, id: str):
        if not re.match("^[A-Za-z0-9_-]+$", id):
            raise ValueError("The custom id {} is not valid!\n"
                             "A custom id can only have numbers, letters and '_' or '-'!".format(id))

    def __str__(self):
        return "ExogenousConfig"

    def __repr__(self):
        return "< " + "ExogenousConfig: " + "" \
               "\nId:" + str(self.__id) + \
               "\nExogenous Technique: " + str(self.__exogenous_technique) + " >"


class ContentAnalyzerConfig(ABC):
    """
    Class that represents the configuration for the content analyzer. The configuration stores the data that
    will be used by the content analyzer main to create contents and process their fields with complex techniques

    Args:
        source (RawInformationSource): raw data source to iterate over for extracting the original contents
        id (Union[str, List[str]]): list of the fields names containing the content's id,
            it's a list instead of single value for handling complex ids composed of multiple fields
        output_directory (str): path of the results serialized content instance
        field_dict (Dict<str, FieldConfig>): stores the config for each field_name the user wants to apply said
            configurations on
        exogenous_representation_list: list of techniques that are used to retrieve exogenous properties that represent
            the contents
    """

    def __init__(self, source: RawInformationSource,
                 id: Union[str, List[str]],
                 output_directory: str,
                 field_dict: Dict[str, List[FieldConfig]] = None,
                 exogenous_representation_list:
                 Union[ExogenousConfig, List[ExogenousConfig]] = None,
                 export_json: bool = False):
        if field_dict is None:
            field_dict = {}
        if exogenous_representation_list is None:
            exogenous_representation_list = []

        self.__source: RawInformationSource = source
        self.__id: List[str] = id
        self.__output_directory: str = output_directory
        self.__field_dict: Dict[str, List[FieldConfig]] = field_dict
        self.__exogenous_representation_list: List[ExogenousPropertiesRetrieval] = exogenous_representation_list
        self.__export_json: bool = export_json

        if not isinstance(self.__exogenous_representation_list, list):
            self.__exogenous_representation_list = [self.__exogenous_representation_list]

        if not isinstance(self.__id, list):
            self.__id = [self.__id]

    @property
    def output_directory(self):
        """
        Getter for the output directory where the produced contents will be stored
        """
        return self.__output_directory

    @property
    def id(self) -> List[str]:
        """
        Getter for the id that represents the ids of the produced contents
        """
        return self.__id

    @property
    def source(self) -> RawInformationSource:
        """
        Getter for the raw information source where the original contents are stored
        """
        return self.__source

    @property
    def exogenous_representation_list(self) -> List[ExogenousConfig]:
        """
        Getter for the exogenous_representation_list
        """
        return self.__exogenous_representation_list

    @property
    def export_json(self) -> bool:
        return self.__export_json

    def get_configs_list(self, field_name: str) -> Iterator[FieldConfig]:
        """
        Getter the list of the field configs specified for the input field

        Args:
            field_name (str): name of the field for which the list of field configs will be retrieved

        Returns:
            Iterator[FieldConfig]: iterator for the field configs specified for the input field
        """
        for config in self.__field_dict[field_name]:
            yield config

    def get_field_name_list(self) -> List[str]:
        """
        Get the list of the field names

        Returns:
            List<str>: list of the field names in the field_dict
        """
        return list(self.__field_dict.keys())

    def add_single_config(self, field_name: str, field_config: FieldConfig):
        """
        Adds a single FieldConfig passed as argument to the FieldConfigs list of the defined field_name.

        Args:
            field_name (str): field name for which the FieldConfig will be added to its config list in the field_dict
            field_config (FieldConfig): FieldConfig instance to append to the config list of the defined field
        """
        # If the field_name is not in the field_dict keys it means there is no list to append the FieldConfig to,
        # so a new list is instantiated
        if self.__field_dict.get(field_name) is not None:
            self.__field_dict[field_name].append(field_config)
        else:
            self.__field_dict[field_name] = list()
            self.__field_dict[field_name].append(field_config)

    def add_multiple_config(self, field_name: str, config_list: List[FieldConfig]):
        """
        Adds multiple FieldConfig for a specific field

        Useful when multiple representations must be specified at once for a field

        Args:
            field_name (str): field_name for which the configuration list will be set in the field_dict
            config_list (List[FieldConfig]): list of FieldConfigs that will be added for a specific field_name
        """
        # If the field_name is not in the field_dict keys it means there is no list to append the FieldConfig to,
        # so a new list is instantiated
        if self.__field_dict.get(field_name) is not None:
            self.__field_dict[field_name].extend(config_list)
        else:
            self.__field_dict[field_name] = list()
            self.__field_dict[field_name].extend(config_list)

    def add_single_exogenous(self, exogenous_config: ExogenousConfig):
        """
        Add the Exogenous Config passed as argument to the exogenous representation list.

        Args:
            exogenous_config (ExogenousConfig): exogenous config instance to append to the exogenous_representation_list
        """
        self.__exogenous_representation_list.append(exogenous_config)

    def add_multiple_exogenous(self, config_list: List[ExogenousConfig]):
        """
        Adds multiple Exogenous Config passed as argument to the exogenous representation list.

        Useful when multiple exogenous techniques must be specified at once

        Args:
            config_list (List[ExogenousConfig]): List of ExogenousConfig that will used to expand the Content
        """
        self.__exogenous_representation_list.extend(config_list)

    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplementedError


class UserAnalyzerConfig(ContentAnalyzerConfig):
    """
        Class that represents the configuration for the content analyzer. The configuration stores the data that
        will be used by the content analyzer main to create contents and process their fields with complex techniques.
        In particular this class refers to users as the content.
    """
    def __str__(self):
        return str(self.__id)

    def __repr__(self):
        msg = "< " + "UserAnalyzerConfig:" +\
              "\nid = " + str(self.__id) + "; " \
              "\nsource = " + str(self.__source) + "; " \
              "\nfield_dict = " + str(self.__field_dict) + "; " \
              "\nexo_representation_list = " + str(self.__exogenous_representation_list) + " >"
        return msg


class ItemAnalyzerConfig(ContentAnalyzerConfig):
    """
        Class that represents the configuration for the content analyzer. The configuration stores the data that
        will be used by the content analyzer main to create contents and process their fields with complex techniques.
        In particular this class refers to items as the content.
    """
    def __str__(self):
        return str(self.__id)

    def __repr__(self):
        msg = "< " + "ItemAnalyzerConfig:" +\
              "\nid = " + str(self.__id) + "; " \
              "\nsource = " + str(self.__source) + "; " \
              "\nfield_dict = " + str(self.__field_dict) + "; " \
              "\nexo_representation_list = " + str(self.__exogenous_representation_list) + " >"
        return msg
