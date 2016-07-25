"""Persistent identifier fetcher."""

from __future__ import absolute_import, print_function

from collections import namedtuple

from .providers import SCOAP3RecordIdProvider

FetchedPID = namedtuple('FetchedPID', ['provider', 'pid_type', 'pid_value'])


def scoap3_recid_fetcher(record_uuid, data):
    """Fetch a record's identifiers."""
    assert "$schema" in data
    assert "control_number" in data
    return FetchedPID(
        provider=SCOAP3RecordIdProvider,
        pid_type=SCOAP3RecordIdProvider.schema_to_pid_type(data['$schema']),
        pid_value=str(data['control_number']),
    )
