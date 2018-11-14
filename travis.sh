#!/bin/sh
set -o errexit
set -o xtrace

pip install -r requirements-test.txt
pip freeze | sort

sh scripts/recreate_records --no-populate
sh scripts/clean_assets
pytest

flake8 .
radon cc --min B .
