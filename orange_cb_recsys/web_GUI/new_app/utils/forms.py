import os
import sys
import errno
from SPARQLWrapper import SPARQLWrapper, JSON

ERROR_INVALID_NAME = 123
ALLOWED_EXTENSIONS = {'csv', 'json', 'dat'}

sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.addDefaultGraph("http://dbpedia.org")


def get_all_dbpedia_types():
    query = "select ?type {"
    query += "   ?type a owl:Class ."
    query += "}"

    _types = []
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        type_ = str(result["type"]["value"])
        data = type_.split('/')
        _types.append(data[4])

    return _types


def get_dbpedia_classes():
    _classes = {}
    _types = get_all_dbpedia_types()

    for index, _type in enumerate(_types):
        _classes[_type] = "_properties"

    return _classes


def is_pathname_valid(pathname: str) -> bool:
    """
    True if the passed pathname is a valid pathname for the current OS;
    False otherwise.
    """

    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        _, pathname = os.path.splitdrive(pathname)

        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)

        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError as exc:
        return False
    else:
        return True


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
