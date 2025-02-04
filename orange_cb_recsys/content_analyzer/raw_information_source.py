import csv
from abc import ABC, abstractmethod

import json
from typing import Dict, Iterator

import mysql.connector


class RawInformationSource(ABC):
    """
    Abstract Class that generalizes the acquisition of raw descriptions of the contents
    from one of the possible acquisition channels.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[Dict[str, str]]:
        """
        Iter on contents in the source,
        each iteration returns a dict representing the raw content
        """
        raise NotImplementedError


class DATFile(RawInformationSource):
    """
    Class for the data acquisition from a DAT file

    Args:
        file_path (str)
    """

    def __init__(self, file_path: str):
        self.__file_path = file_path

    def __iter__(self) -> Iterator[Dict[str, str]]:
        with open(self.__file_path) as f:
            for line in f:
                line_dict = {}
                fields = line.split('::')
                for i, field in enumerate(fields):
                    field = field.strip("\n\t\r")
                    line_dict[str(i)] = field

                yield line_dict


class JSONFile(RawInformationSource):
    """
    Class for the data acquisition from a json file

    Args:
        file_path (str)
    """

    def __init__(self, file_path: str):
        """
        """
        self.__file_path = file_path

    def __iter__(self) -> Iterator[Dict[str, str]]:
        with open(self.__file_path, 'r') as j:
            all_lines = json.load(j, parse_int=str, parse_float=str)
            for line in all_lines:
                yield line


class CSVFile(RawInformationSource):
    """
    Abstract class for the data acquisition from a csv file

    Args:
        file_path (str)
    """

    def __init__(self, file_path: str, has_header: bool = True):
        """
        """
        self.__file_path = file_path
        self.__has_header = has_header

    def __iter__(self) -> Iterator[Dict[str, str]]:
        with open(self.__file_path, newline='', encoding='utf-8-sig') as csv_file:
            if self.__has_header:
                reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
            else:
                reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
                reader.fieldnames = [str(i) for i in range(len(reader.fieldnames))]
                csv_file.seek(0)

            for line in reader:
                yield line


class SQLDatabase(RawInformationSource):
    """
    Abstract class for the data acquisition from a SQL Database

    Args:
        host (str): host ip of the sql server
        username (str): username for the access
        password (str): password for the access
        database_name (str): name of database
        table_name (str): name of the database table where data is stored
    """

    def __init__(self, host: str,
                 username: str,
                 password: str,
                 database_name: str,
                 table_name: str):
        super().__init__()
        self.__host: str = host
        self.__username: str = username
        self.__password: str = password
        self.__database_name: str = database_name
        self.__table_name: str = table_name

        conn = mysql.connector.connect(host=self.__host,
                                       user=self.__username,
                                       password=self.__password)
        cursor = conn.cursor()
        query = """USE """ + self.__database_name + """;"""
        cursor.execute(query)
        conn.commit()
        self.__conn = conn

    @property
    def host(self) -> str:
        return self.__host

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password(self) -> str:
        return self.__password

    @property
    def database_name(self) -> str:
        return self.__database_name

    @property
    def table_name(self) -> str:
        return self.__table_name

    @property
    def conn(self):
        return self.__conn

    @host.setter
    def host(self, host: str):
        self.__host = host

    @username.setter
    def username(self, username: str):
        self.__username = username

    @password.setter
    def password(self, password: str):
        self.__password = password

    @database_name.setter
    def database_name(self, database_name: str):
        self.__database_name = database_name

    @table_name.setter
    def table_name(self, table_name: str):
        self.__table_name = table_name

    @conn.setter
    def conn(self, conn):
        self.__conn = conn

    def __iter__(self) -> Iterator[Dict[str, str]]:
        cursor = self.conn.cursor(dictionary=True)
        query = """SELECT * FROM """ + self.table_name + """;"""
        cursor.execute(query)
        for result in cursor:
            yield result
