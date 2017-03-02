"""Celery tasks for dealing with robotupload."""

from __future__ import absolute_import, print_function

from celery import shared_task

from flask import current_app

from invenio_db import db

from invenio_workflows.proxies import workflow_object_class


@shared_task(ignore_results=True)
def submit_results(results_data=None, errors=[]):
    """Receive the submission of the results of a crawl job.
    Then it spawns the appropiate workflow according to whichever workflow
    the crawl job specifies.
    :param errors: Errors that happened, if any (seems ambiguous)
    :param results_data: Optional data payload with the results list, to skip
        retrieving them from the `results_uri`, useful for slow or unreliable
        storages.
    """
    obj = workflow_object_class.create(data=results_data)
    obj.save()
    db.session.commit()

    obj.start_workflow('upload', delayed=True)

    current_app.logger.info('Parsed {} records.'.format(len([results_data])))
