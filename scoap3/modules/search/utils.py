from elasticsearch_dsl import Q
from flask import current_app
from flask_login import current_user
from inspire_utils.record import get_value
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
