from mock import patch
from pytest import raises

from scoap3.modules.tools.tasks import to_csv, run_tool
from scoap3.modules.tools.tools import get_query_string
from ..test_records import MockApp


def test_to_csv():
    data = {
        'data': [
            [0, 1, 'st r i ng'],
            ['', None, False, True]
        ],
        'header': [
            'a1', 'a s d', False, True
        ]
    }

    expected_result = ('"a1";"a s d";"False";"True"\r\n'
                       '"0";"1";"st r i ng"\r\n'
                       '"";"";"False";"True"\r\n')
    expected_content_type = 'text/csv'

    content_type, result = to_csv(data)
    assert content_type == expected_content_type
    assert result == expected_result


def test_to_csv_invalid_data():
    data = {}

    with raises(ValueError):
        to_csv(data)


def mock_tool_function(argument=None):
    return {
        'header': [argument, 'h1'],
        'data': [['d1', 'd e g y']]
    }


def test_run():
    tool_name = 'func func'
    expected_content_type = 'text/csv'
    expected_recipients = ['TEST_MAIL']
    expected_result_data = '"";"h1"\r\n"d1";"d e g y"\r\n'
    config = {'TOOL_FUNCTIONS': {tool_name: mock_tool_function}}

    with patch('scoap3.modules.tools.tasks.current_app', MockApp(config)),\
            patch('scoap3.modules.tools.tasks.send_result') as send_result:
        run_tool(result_email='TEST_MAIL', tool_name=tool_name)
        send_result.assert_called_with(expected_result_data, expected_content_type, expected_recipients, tool_name)


def test_run_tool_parameter():
    tool_name = 'func func'
    expected_content_type = 'text/csv'
    expected_recipients = ['TEST_MAIL']
    expected_result_data = '"hey";"h1"\r\n"d1";"d e g y"\r\n'
    config = {'TOOL_FUNCTIONS': {tool_name: mock_tool_function}}

    with patch('scoap3.modules.tools.tasks.current_app', MockApp(config)),\
            patch('scoap3.modules.tools.tasks.send_result') as send_result:
        run_tool(result_email='TEST_MAIL', tool_name=tool_name, argument='hey')
        send_result.assert_called_with(expected_result_data, expected_content_type, expected_recipients, tool_name)


def test_query_string():
    assert get_query_string(year=2019, country='CERN') == 'country:CERN AND year:2019'


def test_query_string_none():
    assert get_query_string(year=2019, country=None) == 'year:2019'


def test_query_string_all_none():
    assert get_query_string(year=None, country=None) is None


def test_query_string_all_empty():
    assert get_query_string(year='', country='') is None


def test_query_string_empty():
    assert get_query_string() is None
