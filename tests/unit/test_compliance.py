from scoap3.modules.compliance.models import Compliance


def test_status_change_false():
    c = Compliance()
    c.results = {
        'accepted': False,
    }
    c.history = []

    assert c.has_final_result_changed() is True


def test_status_change_true():
    c = Compliance()
    c.results = {
        'accepted': True,
    }
    c.history = []

    assert c.has_final_result_changed() is True


def test_status_change_history_false():
    c = Compliance()
    c.results = {
        'accepted': False,
    }
    c.history = [
        {'results': {'accepted': False}}
    ]

    assert c.has_final_result_changed() is False


def test_status_change_history_true():
    c = Compliance()
    c.results = {
        'accepted': True,
    }
    c.history = [
        {'results': {'accepted': False}}
    ]

    assert c.has_final_result_changed() is True
