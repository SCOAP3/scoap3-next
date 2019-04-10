from os import walk
from os.path import join, isdir


def get_files(folder):
    """Returns all files recursively in the given folder."""

    if not isdir(folder):
        raise ValueError('%s folder does not exists.' % folder)

    result = []

    for dir, _, filenames in walk(folder):
        files = [join(dir, fn) for fn in filenames]
        result.extend(files)

    return result
