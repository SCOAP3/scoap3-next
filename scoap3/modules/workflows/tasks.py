from datetime import datetime, timedelta

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_workflows import Workflow


@shared_task
def delete_old_workflows():
    days = current_app.config.get('DELETE_WORKFLOWS_OLDER_THEN_DAYS', 60)
    date_to = datetime.now() - timedelta(days=days)
    wokflows = Workflow.query.filter(Workflow.modified <= date_to).all()

    current_app.logger.info('Deleting %d workflows modified before %s.' % (len(wokflows), date_to))

    for w in wokflows:
        try:
            with db.session.begin_nested():
                db.session.delete(w)
            db.session.commit()
        except Exception as e:
            current_app.logger.error('Failed to delete workflow with id "%s". Reason: %s' % (w.uuid, e.message))
