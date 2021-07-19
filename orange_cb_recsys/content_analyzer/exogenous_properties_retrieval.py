import xml
from abc import ABC, abstractmethod
from xml.dom.minidom import Document

import pandas as pd
import numpy as np
from typing import Dict, List, Union
from SPARQLWrapper import SPARQLWrapper, JSON, TSV, CSV, XML, POST, POSTDIRECTLY, JSONLD
from orange_cb_recsys.content_analyzer.raw_information_source import RawInformationSource

from orange_cb_recsys.content_analyzer.content_representation.content import PropertiesDict
from orange_cb_recsys.utils.const import logger


class ExogenousPropertiesRetrieval(ABC):

    def __init__(self, mode: str = 'only_retrieved_evaluated'):
        """
        Class that creates a list of couples like this:
            <property: property value URI>
        The couples are properties retrieved from Linked Open Data Cloud

        Args:
            mode: one in: 'all', 'all_retrieved', 'only_retrieved_evaluated', 'original_retrieved',
        """
        self.__mode = self.__check_mode(mode)

    @staticmethod
    def __check_mode(mode):
        modalities = [
            'all',
            'all_retrieved',
            'only_retrieved_evaluated',
            'original_retrieved',
        ]
        if mode in modalities:
            return mode
        else:
            return 'all'

    @property
    def mode(self):
        return self.__mode

    @mode.setter
    def mode(self, mode):
        self.__mode = self.__check_mode(mode)

    @abstractmethod
    def get_properties(self, raw_source: RawInformationSource) -> List[PropertiesDict]:
        raise NotImplementedError


class PropertiesFromDataset(ExogenousPropertiesRetrieval):
    def __init__(self, mode: str = 'only_retrieved_evaluated', field_name_list: List[str] = None):
        super().__init__(mode)
        self.__field_name_list: List[str] = field_name_list

    def get_properties(self, raw_source: RawInformationSource) -> List[PropertiesDict]:

        logger.info("Extracting exogenous properties from local dataset")
        prop_dict_list = []
        for raw_content in raw_source:

            if self.__field_name_list is None:
                prop_dict = raw_content
            else:
                prop_dict = {field: raw_content[field] for field in self.__field_name_list
                             if raw_content.get(field) is not None}

            if self.mode == 'only_retrieved_evaluated':
                prop_dict = {field: prop_dict[field] for field in prop_dict if prop_dict[field] != ''}

            prop_dict_list.append(PropertiesDict(prop_dict))

        return prop_dict_list


class DBPediaMappingTechnique(ExogenousPropertiesRetrieval):
    """
    Class that creates a list of couples like this:
        <property: property value URI>
    In this implementation the properties are retrieved from DBPedia

    Args:
        entity_type (str): domain of the items that you want to process
        lang (str): lang of the descriptions
        label_field: field to be used as a filter,
            DBPedia node that has the property rdfs:label equal to specified field value
            will be retrieved
        mode: one in: 'all', 'all_retrieved', 'only_retrieved_evaluated', 'original_retrieved',
    """

    def __init__(self, entity_type: str, label_field: str,
                 mode: str = 'only_retrieved_evaluated', prop_as_uri: bool = False):
        super().__init__(mode)

        self.__entity_type = entity_type
        self.__label_field = label_field
        self.__prop_as_uri = prop_as_uri

        self.__sparql = SPARQLWrapper("http://factforge.net/repositories/ff-news")
        self.__sparql.setMethod(POST)
        self.__sparql.setReturnFormat(JSON)

        self.__class_properties = self.__get_properties_class()

    @property
    def label_field(self):
        return self.__label_field

    @label_field.setter
    def label_field(self, label_field: str):
        self.__label_field = label_field

    @property
    def prop_as_uri(self):
        return self.__prop_as_uri

    # INITIAL IDEA ON HOW TO USE ADDITIONAL FILTERS TO RETIREVE CONTENTS
    # def __get_uris_all_contents_with_additional(self, raw_source: RawInformationSource):
        # prefixes = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
        # prefixes += "PREFIX dbo: <http://dbpedia.org/ontology/> "
        # prefixes += "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        # prefixes += "PREFIX foaf: <http://xmlns.com/foaf/0.1/> "
        #
        # all_contents_labels_original_order = [str(raw_content[self.__label_field]) for raw_content in raw_source]
        # all_contents_labels = sorted(all_contents_labels_original_order)
        #
        # values = "VALUES ?contents {" + ' '.join(f'"{wrapped}"' for wrapped in all_contents_labels) + "} "
        #
        # additional_fields_select = [
        #     f"(str(?{self.__additional_filters[prop]}) as ?str_{self.__additional_filters[prop]})"
        #     for prop in self.__additional_filters.keys()]
        #
        # select_clause = f"SELECT ?contents ?uri {' '.join(additional_fields_select)} "
        # where_clause = "WHERE { "
        # optional_clause = "OPTIONAL {"
        # optional_clause += f"?uri rdf:type {self.__entity_type} . " \
        #                    "?uri rdfs:label ?label . " \
        #                    "BIND(str(?label) as ?str_label) " \
        #                    "FILTER(?contents=?str_label) "
        #
        # if self.__additional_filters is not None:
        #     optional_clause += "OPTIONAL { "
        #     additional_fields = ' '.join([f"?uri {prop} ?{self.__additional_filters[prop]} ."
        #                                   for prop in self.__additional_filters.keys()])
        #     optional_clause += additional_fields + "} "
        #
        # optional_clause += "} }"
        #
        # query = prefixes + select_clause + where_clause + values + optional_clause
        #
        # self.__sparql.setQuery(query)
        # results = self.__sparql.query().convert()["results"]["bindings"]
        #
        # contents_taken = sorted([row['contents']['value'] for row in results])
        # while len(contents_taken) < len(all_contents_labels):
        #     contents_missing = all_contents_labels[len(contents_taken):]
        #     values_incomplete = "VALUES ?contents {" + ' '.join(f'"{wrapped}"' for wrapped in contents_missing) + "} "
        #     query_incomplete = prefixes + select_clause + where_clause + values_incomplete + optional_clause
        #
        #     self.__sparql.setQuery(query_incomplete)
        #     result_incomplete = self.__sparql.query().convert()["results"]["bindings"]
        #
        #     results.extend(result_incomplete)
        #     contents_taken.extend([row['contents']['value'] for row in result_incomplete])
        #
        # if len(results) == 0:
        #     raise ValueError("No mapping found")
        #
        # # Reset the order of contents
        # results = sorted(results, key=lambda k: all_contents_labels_original_order.index(k['contents']['value']))
        #
        # uri_lables_dict = {'uri': [], 'label': []}
        # uri_lables_dict.update({additional_field: [] for additional_field in self.__additional_filters.values()})
        # for row in results:
        #     # We are sure there is always the label, it's how the query is built
        #     uri_lables_dict['label'].append(row["contents"]["value"])
        #
        #     if row.get('uri') is not None:
        #         uri_lables_dict['uri'].append(row['uri']['value'])
        #         for additional_field in self.__additional_filters.values():
        #             if row.get('str_' + additional_field) is not None:
        #                 uri_lables_dict[additional_field].append(row['str_' + additional_field]['value'])
        #             else:
        #                 uri_lables_dict[additional_field].append(np.nan)
        #     else:
        #         uri_lables_dict['uri'].append(np.nan)
        #         for additional_field in self.__additional_filters.values():
        #             uri_lables_dict[additional_field].append(np.nan)
        #
        # results_df = pd.DataFrame.from_dict(uri_lables_dict)
        #
        # return results_df

    def __get_uris_all_contents(self, raw_source: RawInformationSource):
        prefixes = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
        prefixes += "PREFIX dbo: <http://dbpedia.org/ontology/> "
        prefixes += "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        prefixes += "PREFIX foaf: <http://xmlns.com/foaf/0.1/> "

        all_contents_labels_original_order = [str(raw_content[self.__label_field]) for raw_content in raw_source]
        all_contents_labels = sorted(all_contents_labels_original_order)

        values = "VALUES ?contents {" + ' '.join(f'"{wrapped}"' for wrapped in all_contents_labels) + "} "

        select_clause = f"SELECT ?contents (sample(?_uri) as ?uri)"
        where_clause = "WHERE { "
        optional_clause = "OPTIONAL {"
        optional_clause += f"?_uri rdf:type {self.__entity_type} . " \
                           "?_uri rdfs:label ?label . " \
                           "BIND(str(?label) as ?str_label) " \
                           "FILTER(?contents=?str_label) "

        optional_clause += "} } GROUP BY ?contents"

        query = prefixes + select_clause + where_clause + values + optional_clause

        self.__sparql.setQuery(query)
        results = self.__sparql.query().convert()["results"]["bindings"]

        contents_taken = sorted([row['contents']['value'] for row in results])
        while len(contents_taken) < len(all_contents_labels):
            contents_missing = all_contents_labels[len(contents_taken):]
            values_incomplete = "VALUES ?contents {" + ' '.join(f'"{wrapped}"' for wrapped in contents_missing) + "} "
            query_incomplete = prefixes + select_clause + where_clause + values_incomplete + optional_clause

            self.__sparql.setQuery(query_incomplete)
            result_incomplete = self.__sparql.query().convert()["results"]["bindings"]

            results.extend(result_incomplete)
            contents_taken.extend([row['contents']['value'] for row in result_incomplete])

        if len(results) == 0:
            raise ValueError("No mapping found")

        # Reset the order of contents
        results = sorted(results, key=lambda k: all_contents_labels_original_order.index(k['contents']['value']))

        uri_lables_dict = {'uri': [], 'label': []}
        for row in results:
            # We are sure there is always the label, it's how the query is built
            uri_lables_dict['label'].append(row["contents"]["value"])

            if row.get('uri') is not None:
                uri_lables_dict['uri'].append(row['uri']['value'])
            else:
                uri_lables_dict['uri'].append(np.nan)

        results_df = pd.DataFrame.from_dict(uri_lables_dict)

        return results_df

    def __get_properties_class(self):
        query = "PREFIX dbo: <http://dbpedia.org/ontology/> "
        query += "SELECT DISTINCT ?property ?property_label WHERE { "
        query += "{ "
        query += "?property rdfs:domain ?class. "
        query += "%s rdfs:subClassOf+ ?class. " % self.__entity_type
        query += "} UNION {"
        query += "?property rdfs:domain %s " % self.__entity_type
        query += "} "
        query += "?property rdfs:label ?property_label. "
        query += f"FILTER (langMatches(lang(?property_label), \"EN\"))." + "} "

        self.__sparql.setQuery(query)
        results = self.__sparql.query().convert()

        if len(results["results"]["bindings"]) == 0:
            raise ValueError("The Entity type doesn't exists in DBPedia!")

        uri_labels_tuples = [(row["property"]["value"], row["property_label"]["value"])
                             for row in results["results"]["bindings"]]

        properties_df = pd.DataFrame.from_records(
            uri_labels_tuples,
            columns=['uri', 'label']
        )

        return properties_df

    def __retrieve_properties_contents(self, uris):
        query = "PREFIX dbo: <http://dbpedia.org/ontology/> "
        query += "SELECT ?uri ?property ?o WHERE { "

        query += "VALUES ?property { "
        query += " ".join([f"<{uri_property}>" for uri_property in self.__class_properties['uri']])
        query += "} "

        query += "VALUES ?uri { "
        query += " ".join([f"<{uri_item}>" for uri_item in uris['uri']])
        query += "} "

        query += "OPTIONAL {?uri ?property ?o . } "
        query += "}"

        self.__sparql.setQuery(query)
        results = self.__sparql.query().convert()

        result_dict = {}
        for row in results["results"]["bindings"]:

            uri_item = row["uri"]["value"]
            property = row["property"]["value"]

            try:
                value = row["o"]["value"]
            except KeyError:
                value = None

            # wrap every property value in a list, in case a property have more than one value
            # eg. starring: [DiCaprio, Tom Hardy]
            if result_dict.get(uri_item) is not None:
                if result_dict[uri_item].get(property) is not None:
                    result_dict[uri_item][property].append(value)
                else:
                    result_dict[uri_item][property] = [value]
            else:
                result_dict[uri_item] = {property: [value]}

        # if some properties have only one value, then remove the list that wraps them
        # eg. director: [Inarritu] -> director: Inarritu
        for uri in result_dict:
            result_dict[uri].update({prop: result_dict[uri][prop][0] for prop in result_dict[uri]
                                     if isinstance(result_dict[uri][prop], list) and len(result_dict[uri][prop]) == 1})

        return result_dict

    def __get_only_retrieved_evaluated(self, uris: pd.DataFrame, all_properties_dbpedia: dict) -> List[PropertiesDict]:

        prop_dict_list = []

        for uri in uris['uri']:

            if pd.notna(uri):

                content_properties_dbpedia = all_properties_dbpedia[uri]

                # Get only retrieved properties that have a value
                if self.prop_as_uri:
                    content_properties_final = {k: content_properties_dbpedia[k] for k in content_properties_dbpedia
                                                if content_properties_dbpedia[k] is not None}
                else:
                    # This goes into the class properties table and gets the labels to the corresponding uri
                    content_properties_final = {
                        self.__class_properties.query('uri == @k')['label'].values[0]: content_properties_dbpedia[k]
                        for k in content_properties_dbpedia
                        if content_properties_dbpedia[k] is not None}

                prop_content = PropertiesDict(content_properties_final)
            else:
                prop_content = PropertiesDict({})

            prop_dict_list.append(prop_content)

        return prop_dict_list

    def __get_all_properties_retrieved(self, uris, all_properties_dbpedia) -> List[PropertiesDict]:
        prop_dict_list = []

        for uri in uris['uri']:

            if pd.notna(uri):

                content_properties_dbpedia = all_properties_dbpedia[uri]

                # Get all retrieved properties, so we substitute those with None with ""
                content_properties_final = {}
                for prop_uri in content_properties_dbpedia:

                    if self.prop_as_uri:
                        value = ''
                        if content_properties_dbpedia.get(prop_uri) is not None:
                            value = content_properties_dbpedia[prop_uri]

                        key = prop_uri
                    else:
                        value = ''
                        if content_properties_dbpedia.get(prop_uri) is not None:
                            value = content_properties_dbpedia[prop_uri]

                        # This goes into the class properties table and gets the labels to the corresponding uri
                        key = self.__class_properties.query('uri == @prop_uri')['label'].values[0]

                    content_properties_final[key] = value

                prop_content = PropertiesDict(content_properties_final)
            else:
                prop_content = PropertiesDict({})

            prop_dict_list.append(prop_content)

        return prop_dict_list

    def __get_original_retrieved(self, uris, all_properties_dbpedia,
                                 raw_source: RawInformationSource) -> List[PropertiesDict]:

        prop_dict_list = []

        for uri, raw_content in zip(uris['uri'], raw_source):

            if pd.notna(uri):

                content_properties_dbpedia = all_properties_dbpedia[uri]
                content_properties_source = raw_content

                # Get all properties from source, those that have value in dbpedia will have value,
                # those that don't have value in dbpedia will be ''
                content_properties_final = {}
                for k in content_properties_source:
                    if k in self.__class_properties['uri'].tolist():
                        value = content_properties_dbpedia[k]

                        if self.prop_as_uri:
                            key = k
                        else:
                            key = self.__class_properties.query('uri == @k')['label'].values[0]
                    elif k in self.__class_properties['label'].tolist():
                        uri = self.__class_properties.query('label == @k')['uri'].values[0]

                        value = content_properties_dbpedia[uri]

                        if self.prop_as_uri:
                            key = uri
                        else:
                            key = k
                    else:
                        value = None
                        key = k

                    if value is None:
                        value = ''

                    content_properties_final[key] = value

                prop_content = PropertiesDict(content_properties_final)
            else:
                prop_content = PropertiesDict({})

            prop_dict_list.append(prop_content)

        return prop_dict_list

    def __get_all_properties(self, uris, all_properties_dbpedia,
                             raw_source: RawInformationSource) -> List[PropertiesDict]:
        prop_dict_list = []

        for uri, raw_content in zip(uris['uri'], raw_source):

            if pd.notna(uri):

                content_properties_dbpedia = all_properties_dbpedia[uri]
                content_properties_source = raw_content

                # Get all properties from source + all properties from dbpedia
                # if there are some properties in source that are also in dbpedia
                # the dbpedia value will overwrite the local source value
                content_properties_final = {}
                for k in content_properties_source:
                    if k in self.__class_properties['uri'].tolist():
                        value = content_properties_dbpedia.pop(k)

                        if self.prop_as_uri:
                            key = k
                        else:
                            key = self.__class_properties.query('uri == @k')['label'].values[0]

                    elif k in self.__class_properties['label'].tolist():
                        uri = self.__class_properties.query('label == @k')['uri'].values[0]

                        value = content_properties_dbpedia.pop(uri)

                        if self.prop_as_uri:
                            key = uri
                        else:
                            key = k
                    else:
                        value = content_properties_source[k]
                        key = k

                    if value is None:
                        value = content_properties_source[k]

                    content_properties_final[key] = value

                for k in content_properties_dbpedia:
                    value = content_properties_dbpedia[k]

                    if value is None:
                        value = ''

                    if self.prop_as_uri:
                        key = k
                    else:
                        key = self.__class_properties.query('uri == @k')['label'].values[0]

                    content_properties_final[key] = value

                prop_content = PropertiesDict(content_properties_final)
            else:
                prop_content = PropertiesDict({})

            prop_dict_list.append(prop_content)

        return prop_dict_list

    def get_properties(self, raw_source: RawInformationSource) -> List[PropertiesDict]:
        """
        Execute the properties couple retrieval

        Args:
            name (str): string identifier of the returned properties object
            raw_content: represent a row in the dataset that
                is being processed

        Returns:
            PropertiesDict
        """
        logger.info("Extracting exogenous properties from DBPedia")
        uris = self.__get_uris_all_contents(raw_source)

        uris_wo_none = uris.dropna()
        all_properties = self.__retrieve_properties_contents(uris_wo_none)

        prop_dict_list = []
        if self.mode == 'only_retrieved_evaluated':
            prop_dict_list = self.__get_only_retrieved_evaluated(uris, all_properties)

        elif self.mode == 'all_retrieved':
            prop_dict_list = self.__get_all_properties_retrieved(uris, all_properties)

        elif self.mode == 'original_retrieved':
            prop_dict_list = self.__get_original_retrieved(uris, all_properties, raw_source)

        elif self.mode == 'all':
            prop_dict_list = self.__get_all_properties(uris, all_properties, raw_source)

        return prop_dict_list
