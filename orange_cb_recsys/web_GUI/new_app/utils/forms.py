import os
import sys
import errno

ERROR_INVALID_NAME = 123
ALLOWED_EXTENSIONS = {'csv', 'json', 'dat'}


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
