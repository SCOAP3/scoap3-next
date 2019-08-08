import csv
from StringIO import StringIO

from elasticsearch_dsl import Q
from flask import current_app, request
from flask_login import current_user
from inspire_utils.record import get_value
from invenio_records_rest.query import default_search_factory
from invenio_search import RecordsSearch


class Scoap3RecordsSearch(RecordsSearch):

    @staticmethod
    def escape_query_string(result):
        query = get_value(result, 'query.query_string.query')

        if query:
            # escape slashes
            result['query']['query_string']['query'] = query.replace('/', '\\/')

        return result

    def to_dict(self, count=False, **kwargs):
        # add _source parameter from url if available
        if not self._source:
            source = request.args.get('_source')
            if source:
                # make sure we have all the required fields
                required_fields = ['control_number', '_updated', '_created']
                self._source = required_fields + source.split(',')

        result = super(Scoap3RecordsSearch, self).to_dict(count, **kwargs)

        # hack: change default value for default_query operator to 'and'
        if 'query_string' in result['query'] and 'default_operator' not in result['query']['query_string']:
            result['query']['query_string']['default_operator'] = 'and'

        # hack: sets fixed page size for not logged in users
        new_size = current_app.config.get('API_UNAUTHENTICATED_PAGE_LIMIT')
        if not current_user.is_authenticated and new_size:
            result['size'] = new_size

        # escape query_string
        self.escape_query_string(result)

        return result


def terms_filter_with_must(field):
    """Create a term filter with AND logical operator instead of or.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """

    def inner(values):
        terms = [Q('term', **{field: value}) for value in values]
        return Q('bool', must=terms)
    return inner


def search_record_from_request():
    """
    Returns ElasticSearch Response instance containing search result.

    The used filters are determined by the HTTP parameters.
    """

    search_index = current_app.config.get('SEARCH_UI_SEARCH_INDEX')
    max_record_count = current_app.config.get('SEARCH_EXPORT_MAX_RECORDS')

    search = Scoap3RecordsSearch(index=search_index)
    search = search[:max_record_count]
    search, _ = default_search_factory(None, search)
    return search, search.execute()


def export_search_result(search, search_result):
    """
    Exports ElasticSearch search result set as csv.

    The field are defined by SEARCH_EXPORT_FIELDS config variable. It is possible to select only a subset
    of these fields using the _source parameter of the search.
    """

    result = StringIO()
    cw = csv.writer(result, delimiter=";", quoting=csv.QUOTE_ALL)

    fields = current_app.config.get('SEARCH_EXPORT_FIELDS')
    if search._source:
        updated_fields = []

        for name, field, key in fields:
            if True in [field in source for source in search._source]:
                updated_fields.append((name, field, key))

        fields = updated_fields

    cw.writerow([name for name, _, _ in fields])

    for hit in search_result.hits:
        row = [unicode(get_value(hit.to_dict(), key, '')).encode("utf-8") for _, _, key in fields]
        cw.writerow(row)

    return result.getvalue()
