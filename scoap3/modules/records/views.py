import json
from datetime import datetime, timedelta

from flask import Blueprint, current_app
from invenio_search import current_search_client

blueprint = Blueprint(
    'scoap3_records',
    __name__,
    template_folder='templates',
)


@blueprint.route('/collections_count')
def collections_count():
    data = {'other': {},
            'journals': {}}

    # generate journal statistics
    journals = current_app.config['JOURNAL_ABBREVIATIONS'].keys()
    for journal in journals:
        data['journals'][journal] = current_search_client.count(q='journal:"%s"' % journal)['count']

    # generate past x days statistics
    dates = {
        'yesterday': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'last_30_days': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'this_year': datetime.now().year,
    }
    for key, date in dates.items():
        data['other'][key] = current_search_client.count(q='record_creation_date:>=%s' % date)['count']

    # all article number
    data['other']['all'] = sum(count for _, count in data['journals'].items())

    return json.dumps(data)
