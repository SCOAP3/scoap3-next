import logging
from os.path import isdir, abspath, isfile, getmtime
from time import sleep

import click
from flask import current_app
from flask.cli import with_appcontext
from inspire_crawler.models import CrawlerJob, JobStatus
from inspire_crawler.tasks import schedule_crawl
from invenio_db import db
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


def schedule_and_wait_crawl(max_wait, *args, **kwargs):
    """
    Calls inspire-crawler schedule_task and waits for the created task to finish.

    :return: if the job finished successfully
    """

    job_id = schedule_crawl(*args, **kwargs)
    log('Crawler job scheduled.', job_id=job_id)
    job = CrawlerJob.get_by_job(job_id)

    sleep_time = current_app.config.get('CLI_HARVEST_SLEEP_TIME', 0.5)
    sleep_counter = 0

    while job.status not in (JobStatus.ERROR, JobStatus.FINISHED):
        if sleep_counter * sleep_time > max_wait:
            log('Timeout reached, skip waiting for job.', logging.ERROR, job_id=job_id, job_status=job.status)
            break

        sleep(sleep_time)
        sleep_counter += 1

        db.session.refresh(job)

    if job.status in (JobStatus.ERROR, JobStatus.FINISHED):
        log('Job finished.', job_id=job_id, job_status=job.status)

    return job.status == JobStatus.FINISHED


def retry_schedule_and_wait_crawl(max_wait, *args, **kwargs):
    """
    Calls schedule_and_wait_crawl and retries if it wasn't successful.

    :return: if the job finished successfully
    """
    max_retries = current_app.config.get('CLI_HARVEST_MAX_RETRIES', 2)

    retries = 0
    while retries < max_retries:
        result = schedule_and_wait_crawl(max_wait, *args, **kwargs)
        if result:
            return True

        retries += 1
        log('Retrying job...', logging.WARNING, current_try=retries, max_retries=max_retries)

    return False


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
@click.option('--max_wait', default=None,
              type=int, help='Maximum time to wait for the crawler to finish in seconds.'
                             ' Uses CLI_HARVEST_MAX_WAIT_TIME value from config if not given.')
def aps(**kwargs):
    """
    Harvests APS through their REST API.

    If no arguments given, it harvests all articles in the 'scoap3' set and sends them to the 'article_upload' workflow.
    This is the default behavior during automatic harvests, but with a from_date specified.
    All arguments are passed to the inspire_craweler and then to the APS spider.

    A new job will only be submitted if the previously submitted job finished (i.e. workflow(s) were created based on
    the Scrapy output). Without this, Scrapy could delete the output files before they got processed, if the workflow
    creation is slower then scraping the packages.
    """
    spider = 'APS'
    workflow = kwargs.pop('workflow')
    max_wait = kwargs.pop('max_wait') or current_app.config.get('CLI_HARVEST_MAX_WAIT_TIME', 60)

    if not retry_schedule_and_wait_crawl(max_wait, spider, workflow, **kwargs):
        log('crawl failed.', logging.ERROR)


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

    A new job will only be submitted if the previously submitted job finished (i.e. workflow(s) were created based on
    the Scrapy output). Without this, Scrapy could delete the output files before they got processed, if the workflow
    creation is slower then scraping the packages.

    Note: the from and until parameters include every article that was created, updated or deleted in the given
    interval. I.e. it is possible to receive an article that was created before the given interval, but updated later.
    """
    spider = 'hindawi'
    list_records_from_dates(spider, **kwargs)


@harvest.command()
@with_appcontext
@click.option('--source_folder', help='All files in the folder will be processed recursively.', required=True)
@click.option('--workflow', default='articles_upload')
@click.option('--max_wait', default=None,
              type=int, help='Maximum time to wait for the crawler to finish in seconds.'
                             ' Uses CLI_HARVEST_MAX_WAIT_TIME value from config if not given.')
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

    A new job will only be submitted if the previously submitted job finished (i.e. workflow(s) were created based on
    the Scrapy output). Without this, Scrapy could delete the output files before they got processed, if the workflow
    creation is slower then scraping the packages.

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
    max_wait = kwargs.pop('max_wait') or current_app.config.get('CLI_HARVEST_MAX_WAIT_TIME', 60)

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
            if not retry_schedule_and_wait_crawl(max_wait, 'OUP', package_path=package_prefix + f, **kwargs):
                log('package failed.', logging.ERROR, path=f)


@harvest.command()
@with_appcontext
@click.option('--source_file', help='File to be processed. This or source_folder parameter has to be present.')
@click.option('--source_folder', help='All files in the folder will be processed recursively. This or source_file '
                                      'parameter has to be present. Packages will be alphabetically ordered '
                                      'regarding their absolute path and then parsed in this order.')
@click.option('--workflow', default='articles_upload')
@click.option('--max_wait', default=None,
              type=int, help='Maximum time to wait for the crawler to finish in seconds.'
                             ' Uses CLI_HARVEST_MAX_WAIT_TIME value from config if not given.')
def springer(source_file, source_folder, workflow, max_wait):
    """
    Harvests Springer packages.

    Exactly one of the source_file and source_folder parameters should be present.

    If a folder is passed, all files within the folder will be parsed and processed. The files will always be processed
    in alphabetical order, so in case an article is available in multiple files, make sure that the alphabetical and
    chronological orders are equivalent. Ignoring this can result in having an older version of an article.

    A new job will only be submitted if the previously submitted job finished (i.e. workflow(s) were created based on
    the Scrapy output). Without this, Scrapy could delete the output files before they got processed, if the workflow
    creation is slower then scraping the packages.
    """
    spider = 'Springer'
    package_prefix = 'file://'
    max_wait = max_wait or current_app.config.get('CLI_HARVEST_MAX_WAIT_TIME', 60)

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
        if not retry_schedule_and_wait_crawl(max_wait, spider, workflow, package_path=package_prefix + path):
            log('package failed.', logging.ERROR, path=path)


@harvest.command()
@with_appcontext
@click.option('--source_file', help='File to be processed. This or source_folder parameter has to be present.')
@click.option('--source_folder', help='All files in the folder will be processed recursively. This or source_file '
                                      'parameter has to be present. Packages will be alphabetically ordered '
                                      'regarding their absolute path and then parsed in this order.')
@click.option('--workflow', default='articles_upload')
@click.option('--max_wait', default=None,
              type=int, help='Maximum time to wait for the crawler to finish in seconds.'
                             ' Uses CLI_HARVEST_MAX_WAIT_TIME value from config if not given.')
def elsevier(source_file, source_folder, workflow, max_wait):
    """
    Harvests Elsevier packages.

    Exactly one of the source_file and source_folder parameters should be present.

    If a folder is passed, all files within the folder will be parsed and processed. The files will be sorted by
    modification date and processed in that order. Incorrect modification dates can result in having an older version
    of an article.

    A new job will only be submitted if the previously submitted job finished (i.e. workflow(s) were created based on
    the Scrapy output). Without this, Scrapy could delete the output files before they got processed, if the workflow
    creation is slower then scraping the packages.
    """
    spider = 'Elsevier'
    package_prefix = 'file://'
    max_wait = max_wait or current_app.config.get('CLI_HARVEST_MAX_WAIT_TIME', 60)

    entries = get_packages_for_file_or_folder(source_file, source_folder)

    if not entries:
        log('No entries, abort.', logging.ERROR)
        return

    # sorting files by their modification date
    timed_entries = [(getmtime(f), f) for f in entries if isfile(f)]
    sorted_entries = sorted(timed_entries)
    sorted_entries = [e[1] for e in sorted_entries]

    # harvesting all packages found in source folder
    entries_count = len(sorted_entries)
    log('Processing packages...', entry_count=entries_count)
    for i, path in enumerate(sorted_entries):
        log('processing package', path=path, current_index=i, entry_count=entries_count)
        if not retry_schedule_and_wait_crawl(max_wait, spider, workflow, package_path=package_prefix + path):
            log('package failed.', logging.ERROR, path=path)
