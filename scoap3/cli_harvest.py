import logging
from os.path import isdir, abspath, isfile

import click
from flask.cli import with_appcontext
from inspire_crawler.tasks import schedule_crawl
from invenio_oaiharvester.tasks import list_records_from_dates

from scoap3.modules.records.util import create_from_json
from scoap3.modules.robotupload.util import parse_received_package
from scoap3.utils.file import get_files
from scoap3.utils.helpers import clean_oup_package_name

logger = logging.getLogger(__name__)


def log(msg='', level=logging.INFO, **kwargs):
    params = ('%s=%s' % (x[0], x[1]) for x in kwargs.items())
    logger.log(level, msg + '\t' + '\t'.join(params))


def get_packages_for_file_or_folder(source_file, source_folder):
    """
    Collects all the files based on given parameters. Exactly one of the parameters has to be specified.

    If source_file is given, it will return with a list containing source_file.
    If source_folder is given, it will search recursively all files in the directory and return the list of found files.
    """

    if not bool(source_folder) ^ bool(source_file):
        log('Source_folder XOR source_file has to be specified, exactly one of them.', logging.ERROR,
            source_file=source_file, source_folder=source_folder)
        return ()

    # validate path parameters, collect packages
    entries = ()
    if source_file:
        source = abspath(source_file)
        if isfile(source):
            entries = [source]
        else:
            log('Source file does not exist', logging.ERROR)
    else:
        source = abspath(source_folder)
        if isdir(source):
            entries = get_files(source)
        else:
            log('Source folder does not exist', logging.ERROR)

    return entries


@click.group()
def harvest():
    """ Manual harvest commands. USE AT YOUR OWN RISK. You've been warned."""


@harvest.command()
@with_appcontext
@click.option('--source_file', help='File to be processed. This or source_folder parameter has to be present.')
@click.option('--source_folder', help='All files in the folder will be processed recursively. '
                                      'This or source_file parameter has to be present.Packages will be alphabetically '
                                      'ordered regarding their absolute path and then parsed in this order.')
def acta_cpc(source_file, source_folder):
    """
    Harvests Acta Physica Polonica B or Chinese Physics C packages.

    Passed files should contain pushed metadata in xml format.
    Exactly one of the source_file and source_folder parameters should be present.

    If a folder is passed, all files within the folder will be parsed and processed. The files will always be processed
    in alphabetical order, so in case an article is available in multiple files, make sure that the alphabetical and
    chronological orders are equivalent. Ignoring this can result in having an older version of an article.
    """

    entries = get_packages_for_file_or_folder(source_file, source_folder)

    if not entries:
        log('No entries, abort.', logging.ERROR)
        return

    # harvesting all packages found in source folder
    # sorting like this will result in a chronological order, because the filename contains
    # the date and time of delivery.
    entries_count = len(entries)
    log('Processing packages...', entry_count=entries_count)
    for i, path in enumerate(sorted(entries)):
        if not isfile(path):
            log('Path not a file. Skipping.', path=path)
            continue

        log('processing package', path=path, current_index=i, entry_count=entries_count)
        with open(path, 'rt') as f:
            file_data = f.read()
            obj = parse_received_package(file_data, path)

            create_from_json({'records': [obj]}, apply_async=False)


@harvest.command()
@with_appcontext
@click.option('--from_date', default=None)
@click.option('--until_date', default=None)
@click.option('--sets', default='scoap3')
@click.option('--workflow', default='articles_upload')
def aps(**kwargs):
    """
    Harvests APS through their REST API.

    If no arguments given, it harvests all articles in the 'scoap3' set and sends them to the 'article_upload' workflow.
    This is the default behavior during automatic harvests, but with a from_date specified.
    All arguments are passed to the inspire_craweler and then to the APS spider.
    """
    spider = 'APS'
    workflow = kwargs.pop('workflow')
    schedule_crawl(spider, workflow, **kwargs)


@harvest.command()
@with_appcontext
@click.option('--from_date', default=None)
@click.option('--until_date', default=None)
@click.option('--url', default='https://www.hindawi.com/oai-pmh/oai.aspx')
@click.option('--workflow', default='articles_upload')
@click.option('--setspecs', default='HINDAWI.AHEP')
@click.option('--metadata_prefix', default='marc21')
def hindawi(**kwargs):
    """
    Harvests APS through their REST API.

    If no arguments given, it harvests all articles in the 'scoap3' set and sends them to the 'article_upload' workflow.
    This is the default behavior during automatic harvests, but with a from_date specified.

    All arguments are passed to the inspire_craweler and then to the APS spider.

    Note: the from and until parameters include every article that was created, updated or deleted in the given
    interval. I.e. it is possible to receive an article that was created before the given interval, but updated later.
    """

    list_records_from_dates(spider='hindawi', **kwargs)


@harvest.command()
@with_appcontext
@click.option('--source_folder', help='All files in the folder will be processed recursively.', required=True)
@click.option('--workflow', default='articles_upload')
def oup(**kwargs):
    """
    Harvests OUP packages.

    OUP delivers articles in multiple zip files, so *one package* consists of four zip archives:
      1) containing pdfa full text files ('_archival.zip' postfix)
      2) containing images ('.img.zip' postfix)
      3) containing pdf full text files ('.pdf.zip' postfix)
      4) containing xml metadata files ('.xml.zip' postfix)
    These archives can contain information/files about more then one article.

    Processing the files of a package in a proper order is crucial: when a non-xml file is parsed, it will only be
    unzipped to the corresponding directory. However when the xml file is parsed a workflow will be scheduled, which
    will be expecting the files to be in the correct place.

    Since the alphabetical sort does not provide this order, the given files in a folder will be grouped together
    by removing the postfix from the filename.

    The packages will be processed in alphabetical order. To make sure the newest article is available for each article
    after the process, ensure that the chronological and alphabetical order of the packages are equivalent. E.g. have
    the date and time of delivery in the beginning of the filename.

    The following examples demonstrate the expected folder structure and file naming.

    Examples 1 (next):
        In case of having the following files:
        harvest/
            - 20190331195346-ptep_iss_2019_3.img.zip
            - 20190331195346-ptep_iss_2019_3.pdf.zip
            - 20190331195346-ptep_iss_2019_3.xml.zip
            - 20190331195346-ptep_iss_2019_3_archival.zip
            - 20190228130556-ptep_iss_2019_2.img.zip
            - 20190228130556-ptep_iss_2019_2.pdf.zip
            - 20190228130556-ptep_iss_2019_2.xml.zip
            - 20190228130556-ptep_iss_2019_2_archival.zip

        the following command can be used:
        `scoap3 harvest oup --source_folder harvest`

    Examples 2 (legacy):
        In case of having the following files:
        harvest/
            - 2019-03-30_16:30:41_ptep_iss_2019_3.img.zip
            - 2019-03-30_16:30:41_ptep_iss_2019_3.pdf.zip
            - 2019-03-30_16:30:41_ptep_iss_2019_3_archival.zip
            - 2019-03-30_16:30:41_ptep_iss_2019_3.xml.zip
            - 2019-01-30_15:30:31_ptep_iss_2018_6.img.zip
            - 2019-01-30_15:30:31_ptep_iss_2018_6.pdf.zip
            - 2019-01-30_15:30:31_ptep_iss_2018_6_archival.zip
            - 2019-01-30_15:30:31_ptep_iss_2018_6.xml.zip

        the following command can be used:
        `scoap3 harvest oup --source_folder harvest`
    """

    package_prefix = 'file://'
    source_folder = kwargs.pop('source_folder')

    # validate path parameters, collect packages
    packages = []
    source = abspath(source_folder)
    if isdir(source):
        packages = get_files(source)
    else:
        log('Source folder does not exist', logging.ERROR)

    if not packages:
        log('No packages, abort.', logging.ERROR)
        return

    # group collected packages
    log('grouping files...')
    grouped_packages = {}
    for package in packages:
        if not package.endswith('.zip'):
            log('package should be a .zip file. Skipping.', package_path=package)
            continue

        group_key = clean_oup_package_name(package)
        if group_key not in grouped_packages:
            grouped_packages[group_key] = {'files': []}

        if package.endswith('.xml.zip') or package.endswith('.xml_v1.zip'):
            grouped_packages[group_key]['xml'] = package
        else:
            grouped_packages[group_key]['files'].append(package)

    log('sorting grouped files...')
    sorted_grouped_packages = sorted(grouped_packages.items())

    # schedule crawls on the sorted packages
    for group_key, package in sorted_grouped_packages:
        if 'xml' not in package:
            log('No xml file, skipping package.', logging.ERROR, package=package, group_key=group_key)
            continue

        for f in package.get('files', []) + [package['xml']]:
            log('scheduling...', package_path=f)
            schedule_crawl(spider='OUP', package_path=package_prefix + f, **kwargs)


@harvest.command()
@with_appcontext
@click.option('--source_file', help='File to be processed. This or source_folder parameter has to be present.')
@click.option('--source_folder', help='All files in the folder will be processed recursively. This or source_file '
                                      'parameter has to be present. Packages will be alphabetically ordered '
                                      'regarding their absolute path and then parsed in this order.')
@click.option('--workflow', default='articles_upload')
def springer(source_file, source_folder, workflow):
    """
    Harvests Springer packages.

    Exactly one of the source_file and source_folder parameters should be present.

    If a folder is passed, all files within the folder will be parsed and processed. The files will always be processed
    in alphabetical order, so in case an article is available in multiple files, make sure that the alphabetical and
    chronological orders are equivalent. Ignoring this can result in having an older version of an article.
    """
    spider = 'Springer'
    package_prefix = 'file://'

    entries = get_packages_for_file_or_folder(source_file, source_folder)

    if not entries:
        log('No entries, abort.', logging.ERROR)
        return

    # harvesting all packages found in source folder
    # sorting like this will result in a chronological order, because the filename contains
    # the date and time of delivery.
    entries_count = len(entries)
    log('Processing packages...', entry_count=entries_count)
    for i, path in enumerate(sorted(entries)):
        if not isfile(path):
            log('Path not a file. Skipping.', path=path)
            continue

        log('processing package', path=path, current_index=i, entry_count=entries_count)
        schedule_crawl(spider=spider, package_path=package_prefix + path, workflow=workflow)
