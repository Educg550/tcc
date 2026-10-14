import urllib.parse

import requests
import pytest

@pytest.mark.dependency()
class TestIdentity():
    session = {}

    @pytest.mark.dependency(name="test_unauthorized_route")
    def test_unauthorized_route(self, client):
        response = client.get('/form/create')
        assert response.status_code == 401

    @pytest.mark.dependency(name="test_login", depends=["test_unauthorized_route"])
    def test_login(self, client, pytestconfig):
        with client.session_transaction() as session:
            session.clear()

        response_senhaunica = client.get('/login/senhaunica')

        assert response_senhaunica.status_code == 302

        url_uspdigital = response_senhaunica.headers["Location"]
        with client.session_transaction() as session:
            assert 'request_secret' in session

        query_str = url_uspdigital.split('?')[-1]
        queries = urllib.parse.parse_qs(query_str)
        payload = { 
            "loginUsuario": pytestconfig.getoption("--login"), 
            "senhaUsuario": pytestconfig.getoption("--password"),
            "oauth_token": queries["oauth_token"]
        }
        headers = { "Content-Type": "application/x-www-form-urlencoded" }
        response_uspdigital = requests.post(url_uspdigital, data=payload, headers=headers, allow_redirects=False)

        assert response_uspdigital.status_code == 302
        
        url_senhaunica = response_uspdigital.headers["Location"]
        query_str = url_senhaunica.split('?')[-1]
        client.get('/login/senhaunica?' + query_str)

        with client.session_transaction() as session:
            assert 'access_secret' in session
            assert 'access_token' in session
            self.session["access_secret"] = session["access_secret"]
            self.session["access_token"] = session["access_token"]

        pass

    @pytest.mark.dependency(depends=["test_login"])
    def test_authorized_route(self, client):
        with client.session_transaction() as session:
            session["access_secret"] = self.session["access_secret"]
            session["access_token"] = self.session["access_token"]

        response = client.get('/form/create')
        assert response.status_code == 200