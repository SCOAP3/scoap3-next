import json
import logging
from os import listdir
from os.path import join, isdir, abspath, isfile, realpath, dirname

import click
from flask.cli import with_appcontext
from inspire_crawler.tasks import schedule_crawl
from invenio_oaiharvester.tasks import list_records_from_dates
from jsonschema import validate, ValidationError, SchemaError

from scoap3.modules.records.util import create_from_json
from scoap3.modules.robotupload.util import parse_received_package

logger = logging.getLogger(__name__)


def log(msg='', level=logging.INFO, **kwargs):
    params = ('%s=%s' % (x[0], x[1]) for x in kwargs.items())
    logger.log(level, msg + '\t' + '\t'.join(params))


def validate_schema(obj):
    key = '$schema'

    if key not in obj:
        log('No schema found!', logging.WARNING, obj=obj)
        return True

    schema_path = join(dirname(realpath(__file__)), 'modules', 'records', 'jsonschemas', 'hep.json')
    with open(schema_path, 'rt') as f:
        schema_data = json.loads(f.read())

    try:
        validate(obj, schema_data)
    except (ValidationError, SchemaError) as err:
        log('validation error!', logging.ERROR, err=err)
        return False

    return True


@click.group()
def harvest():
    """
    Manual harvest commands.
    USE AT YOUR OWN RISK. You've been warned.
    """


@harvest.command()
@with_appcontext
@click.option('--source_file', help='File to be processed.')
@click.option('--source_folder', help='All files in the folder will be processed.')
def acta_cpc(source_file, source_folder):
    """
    Harvests Acta Physica Polonica B or Chinese Physics C packages.
    Passed packages should contain pushed metadata in xml format.
    If a folder is passed, all files within the folder will be parsed and uploaded.
    """

    if (source_folder and source_file) or not(source_folder or source_file):
        log('Source_folder XOR source_file has to be specified, exactly one of them.', logging.ERROR,
            source_file=source_file, source_folder=source_folder)
        return

    # validate path parameters, collect packages
    entries = None
    if source_file:
        source = abspath(source_file)
        if isfile(source):
            entries = [source]
        else:
            log('Source file does not exist', logging.ERROR)
    else:
        source = abspath(source_folder)
        if isdir(source_folder):
            # sorting like this will result in a chronological order, because the filename contains
            # the date and time of delivery.
            entries = sorted(listdir(source_folder))
        else:
            log('Source folder does not exist', logging.ERROR)

    if not entries:
        log('No entries, abort.', logging.ERROR)
        return

    # harvesting all packages found in source folder
    entries_count = len(entries)
    log('Processing packages...', entry_count=entries_count, source_folder=source)
    for i, entry in enumerate(entries):
        path = join(source, entry)
        if not isfile(path):
            log('Path not a file. Skipping.', path=path)
            continue

        log('processing package', path=path, current_index=i, entry_count=entries_count)
        with open(path, 'rt') as f:
            file_data = f.read()
            obj = parse_received_package(file_data, entry)
            if not validate_schema(obj):
                log('Schema not valid.', logging.ERROR)
            create_from_json({'records': [obj]}, apply_async=False)


@harvest.command()
@with_appcontext
@click.option('--from_date', default=None)
@click.option('--until_date', default=None)
@click.option('--sets', default='scoap3')
@click.option('--spider', default='APS')
@click.option('--workflow', default='articles_upload')
def aps(**kwargs):
    """
    Harvests APS through their REST API .
    If no arguments given, it harvests all articles in the 'scoap3' set and sends them to the 'article_upload' workflow.
    All arguments are just passed to the inspire_craweler and then to the APS spider.
    """
    spider = kwargs.pop('spider')
    workflow = kwargs.pop('workflow')
    schedule_crawl(spider, workflow, **kwargs)


@harvest.command()
@with_appcontext
@click.option('--from_date', default=None)
@click.option('--until_date', default=None)
@click.option('--url', default='https://www.hindawi.com/oai-pmh/oai.aspx')
@click.option('--spider', default='hindawi')
@click.option('--workflow', default='articles_upload')
@click.option('--setspecs', default='HINDAWI.AHEP')
@click.option('--metadata_prefix', default='marc21')
def hindawi(**kwargs):
    """
    Harvests APS through their REST API .
    If no arguments given, it harvests all articles in the 'scoap3' set and sends them to the 'article_upload' workflow.
    All arguments are just passed to the inspire_craweler and then to the APS spider.

    Note: the from and until parameters include every article that was created, updated or deleted in the given
    interval.
    """

    list_records_from_dates(**kwargs)
