import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from unittest.mock import patch

from webapp.app import app

@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_invalid(client):
    with patch('webapp.app.set_login_credentials', return_value=False):
        resp = client.post('/login', json={'id': 'u', 'password': 'p'})
        assert resp.status_code == 400
        assert resp.get_json()['message'] == 'Invalid credentials'

def test_search_internal_error(client):
    with patch('webapp.app.search_trains', side_effect=RuntimeError('boom')):
        resp = client.get('/reserve?departure=A&arrival=B&date=20230101')
        assert resp.status_code == 500
        assert resp.get_json()['message'] == 'boom'

def test_card_settings_missing_field(client):
    resp = client.post('/settings/card', json={'password': 'p'})
    assert resp.status_code == 400
    assert 'Missing field' in resp.get_json()['message']
