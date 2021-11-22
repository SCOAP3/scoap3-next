#!/bin/sh
set -o errexit
set -o xtrace

pip install -r requirements-test.txt -e .
pip freeze | sort

pytest

flake8 scoap3/
radon cc --min B .
