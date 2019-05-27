import json
from os import path
from os.path import join


def get_response_dir():
    return path.dirname(path.realpath(__file__))


def read_hep_schema():
    with open(join(get_response_dir(), 'jsonschemas', 'hep.json'), 'rb') as f:
        return f.read()


def read_titles_schema():
    with open(join(get_response_dir(), 'jsonschemas', 'elements', 'titles.json'), 'rb') as f:
        return f.read()


def read_response(folder, input_filename):
    file_path = path.join(get_response_dir(), folder, input_filename)
    with open(file_path, 'rb') as f:
        return f.read()


def read_response_as_json(folder, input_json_filename):
    file_path = path.join(get_response_dir(), folder, input_json_filename)
    with open(file_path, 'rt') as f:
        return json.loads(f.read())
