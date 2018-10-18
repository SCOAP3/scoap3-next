from flask import current_app
from flask_login import current_user
from invenio_search import RecordsSearch


class Scoap3RecordsSearch(RecordsSearch):

    def to_dict(self, count=False, **kwargs):
        result = super(Scoap3RecordsSearch, self).to_dict(count, **kwargs)

        # hack: change default value for default_query operator to 'and'
        if 'query_string' in result['query'] and 'default_operator' not in result['query']['query_string']:
            result['query']['query_string']['default_operator'] = 'and'

        # hack: sets fixed page size for not logged in users
        new_size = current_app.config.get('API_UNAUTHENTICATED_PAGE_LIMIT')
        if not current_user.is_authenticated and new_size:
            result['size'] = new_size

        return result
