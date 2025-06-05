import os, sys

# Use an in-memory keyring so tests don't require system backends
os.environ.setdefault("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from unittest.mock import patch

from webapp.app import app, AUTH_TOKEN

@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_invalid(client):
    with patch('webapp.app.set_login_credentials', return_value=False):
        resp = client.post(
            '/login',
            json={'id': 'u', 'password': 'p'},
            headers={'X-Auth-Token': AUTH_TOKEN}
        )
        assert resp.status_code == 400
        assert resp.get_json()['message'] == 'Invalid credentials'

def test_search_internal_error(client):
    with patch('webapp.app.search_trains', side_effect=RuntimeError('boom')):
        resp = client.get(
            '/reserve?departure=A&arrival=B&date=20230101',
            headers={'X-Auth-Token': AUTH_TOKEN}
        )
        assert resp.status_code == 500
        assert resp.get_json()['message'] == 'boom'

def test_card_settings_missing_field(client):
    resp = client.post(
        '/settings/card',
        json={'password': 'p'},
        headers={'X-Auth-Token': AUTH_TOKEN}
    )
    assert resp.status_code == 400
    assert 'Missing field' in resp.get_json()['message']


def test_login_success(client):
    with patch('webapp.app.set_login_credentials', return_value=True):
        resp = client.post(
            '/login',
            json={'id': 'u', 'password': 'p'},
            headers={'X-Auth-Token': AUTH_TOKEN}
        )
        assert resp.status_code == 200
        assert resp.get_json()['message'] == 'ok'


def test_reserve_missing_field(client):
    resp = client.post(
        '/reserve',
        json={'departure': 'A'},
        headers={'X-Auth-Token': AUTH_TOKEN}
    )
    assert resp.status_code == 400
    assert 'Missing field' in resp.get_json()['message']


def test_search_default_flags(client):
    with patch('webapp.app.search_trains', return_value=[]) as mock:
        resp = client.get(
            '/reserve?departure=A&arrival=B&date=20230101',
            headers={'X-Auth-Token': AUTH_TOKEN}
        )
        assert resp.status_code == 200
        mock.assert_called_once_with(
            'SRT', 'A', 'B', '20230101', '000000',
            include_no_seats=False, include_waiting_list=False
        )


def test_search_flags_forwarded(client):
    with patch('webapp.app.search_trains', return_value=[]) as mock:
        resp = client.get(
            '/reserve?departure=A&arrival=B&date=20230101&rail_type=KTX&include_no_seats=1&include_waiting_list=true',
            headers={'X-Auth-Token': AUTH_TOKEN}
        )
        assert resp.status_code == 200
        mock.assert_called_once_with(
            'KTX', 'A', 'B', '20230101', '000000',
            include_no_seats=True, include_waiting_list=True
        )
