from __future__ import absolute_import, print_function

import logging

from celery import shared_task
from flask import current_app
from inspire_utils.record import get_value
from invenio_mail.api import TemplatedMessage

from scoap3.modules.records.util import is_doi_in_db
from scoap3.utils.arxiv import get_arxiv_categories
from scoap3.utils.crossref import get_crossref_items, parse_date_parts
from scoap3.utils.date import datetime
from scoap3.utils.inspire import get_inspire_arxiv_categories_for_record

logger = logging.getLogger(__name__)


def _get_pubdate_from_crossref_message(journal, api_message):
    """Retrieves publication date for an article."""
    if journal == 'Progress of Theoretical and Experimental Physics':
        parts = api_message['published-online']['date-parts'][0]
        return parse_date_parts(parts)

    return parse_date_parts(api_message['created']['date-parts'][0])


def _get_arxiv_category_from_arxiv(item):
    """
    Try querying arXiv for the category.

    Hence the arXiv id is not present at this point, try filter for doi or title.
    """
    field_list = (('doi', 'DOI'), ('title', 'title[0]'))
    for param, item_key in field_list:
        categories = get_arxiv_categories(**{param: get_value(item, item_key)})
        if categories:
            return categories[0]

    return None


def _get_arxiv_category(item):
    """Tries to retrieve arXiv id for an article.

    First based on the DOI, if that fails, based on the title.
    """

    doi = item['DOI']

    # try to acquire arxiv category from inspire
    categories = get_inspire_arxiv_categories_for_record('doi:%s' % doi)
    if categories:
        return categories[0]

    logger.warning('arXiv category not found in INSPIRE. doi=%s' % doi)

    return _get_arxiv_category_from_arxiv(item)


def _send_article_check_report(missing_articles, statistics, from_date):
    """Sends detailed report regarding the missing articles."""
    msg = TemplatedMessage(
        template_html='scoap3_records/email/article_check_report.html',
        subject='SCOAP3 - Article check report',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=current_app.config.get('OPERATIONS_EMAILS'),
        ctx={
            'missing_articles': missing_articles,
            'statistics': statistics,
            'from_date': from_date
        }
    )
    current_app.extensions['mail'].send(msg)


def perform_article_check_for_journal(from_date, journal, cooperation_dates):
    """Compare the articles on crossref.org and in our database to find missing ones for the given journal.

    Queries all article from crossref after the given date in the given journal. Filters out articles that have been
    published too early or late according to cooperation_dates values. Then it validates if the article is a hep
    article (this step is skipped for journals not in ARTICLE_CHECK_HAS_TO_BE_HEP. Finally if the article
    should be present in our database, it checks if it really is.

    :param from_date: day from which it starts the comparision.
    :param journal: formal name of the journal. Will be used as a filter parameter.
    :param cooperation_dates: (from_date, end_date) tuple containing datetime objects.
    :return: (journal_stats, missing_records) tuple. Containing overview stats about the process and
    detailed info about missing articles.
    """
    hep_journals = current_app.config.get('ARTICLE_CHECK_HAS_TO_BE_HEP')

    # statistics to be collected during the process for the journal
    journal_stats = {
        'journal': journal,
        'outside_cooperation_dates': 0,
        'no_arxiv_category': 0,
        'non_hep_arxiv_category': 0,
        'in_db': 0,
        'missing': 0
    }
    missing_records = []

    # unpack cooperation dates
    cooperation_dates_from, cooperation_dates_to = cooperation_dates
    if cooperation_dates_from is None and cooperation_dates_to is None:
        logger.warning('Cooperation dates for journal "%s" not provided.' % journal)

    ignore_after_datetime = datetime.now() - current_app.config.get('ARTICLE_CHECK_IGNORE_TIME')

    filter_param = 'from-pub-date:%s,container-title:%s' % (from_date, journal)
    # process all articles in the given journal
    for item in get_crossref_items(filter_param):
        doi = item['DOI']

        # check the publication date of the given article
        pub_date = _get_pubdate_from_crossref_message(journal, item)
        if (cooperation_dates_from is not None and cooperation_dates_from > pub_date) or (
                cooperation_dates_to is not None and cooperation_dates_to < pub_date):
            logger.info('Journal outside of cooperation dates. doi=%s journal=%s pubdate=%s' % (
                doi, journal, pub_date))
            journal_stats['outside_cooperation_dates'] += 1
            continue

        # if an article was published too recently, it shouldn't be reported
        if pub_date >= ignore_after_datetime:
            logger.info('Skipping article because it was published too recentry. doi=%s journal=%s pubdate=%s' % (
                doi, journal, pub_date))
            continue

        # if we are only interested in hep articles, check arxiv category
        if journal in hep_journals:
            category = _get_arxiv_category(item)
            if not category:
                logger.info('Could not determine arxiv category. doi=%s journal=%s pubdate=%s' % (
                    doi, journal, pub_date))
                journal_stats['no_arxiv_category'] += 1
                continue

            if category[:3] != 'hep':
                logger.info('Not "hep*" arxiv category. doi=%s journal=%s pubdate=%s category=%s' % (
                    doi, journal, pub_date, category))
                journal_stats['non_hep_arxiv_category'] += 1
                continue
        else:
            logger.info('Article is part of a not only hep journal. Skipping arXiv category check. '
                        'doi=%s journal=%s' % (doi, journal))

        # check if the article is in our database
        if is_doi_in_db(doi):
            journal_stats['in_db'] += 1
            logger.info('Article is in db. doi=%s journal=%s' % (doi, journal))
        else:
            journal_stats['missing'] += 1
            missing_records.append((doi, item['title'][0]))
            logger.info('Article is missing. doi=%s journal=%s' % (doi, journal))

    return journal_stats, missing_records


@shared_task(ignore_results=True)
def perform_article_check(from_date=None):
    """Compare the articles on crossref.org and in our database to find missing ones.

    Queries all article from crossref after the given date. Filters out articles that have been published
    too early or late according to ARTICLE_CHECK_JOURNALS values. Then it validates if the article is a hep
    article (this step is skipped for journals not in ARTICLE_CHECK_HAS_TO_BE_HEP. Finally if this article
    should be present in our database, it checks if is.

    After checking all journals, a summary will be sent to OPERATIONS_EMAILS.

    :param from_date: day from which it starts the comparision.
                      If not given, Now - settings.ARTICLE_CHECK_DEFAULT_TIME_DELTA is used.
    """

    if not from_date:
        from_date = datetime.now().date() - current_app.config.get('ARTICLE_CHECK_DEFAULT_TIME_DELTA')

    journals = current_app.config.get('ARTICLE_CHECK_JOURNALS')

    missing_records = []
    statistics = []
    for journal, cooperation_dates in journals.items():
        journal_stats, journal_missing_records = perform_article_check_for_journal(from_date, journal,
                                                                                   cooperation_dates)

        statistics.append(journal_stats)
        missing_records.extend(journal_missing_records)

    _send_article_check_report(missing_records, statistics, from_date)
