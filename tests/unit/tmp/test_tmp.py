"""Unit tests for the stats utils."""

from __future__ import absolute_import, division, print_function


def test_true():
    assert True


def test_false():
    assert not False


def test_scoap3(app):
    assert app.config
