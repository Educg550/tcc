import json
import pytest

from test_identity import TestIdentity

@pytest.mark.dependency(depends=["test_login"])
class TestApp():
    def test_create_form(self, client):
        with client.session_transaction() as session:
            session["access_secret"] = TestIdentity.session["access_secret"]
            session["access_token"] = TestIdentity.session["access_token"]

        response = client.get('/form/create')
        csrf_token = None
        set_cookies = response.headers.getlist('Set-Cookie')
        for cookie in set_cookies:
            if cookie.startswith('_csrf_token='):
                csrf_token = cookie.split(';')[0].split('=')[1]
                break

        assert csrf_token is not None, "Token CSRF não encontrado no cookie."

        headers = { 
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf_token
        }

        # not sections form payload
        payload = {
            "form": json.dumps({ 
                "title": "Title - not sections form payload"
            }),
            "_csrf_token": csrf_token
        }
        response = client.post('/form/create', data=payload, headers=headers)
        assert response.status_code == 302

        # sections not required
        payload = {
            "form": json.dumps({ 
                "title": "Title - not sections form payload",
                "sections": []
            }),
            "_csrf_token": csrf_token
        }
        response = client.post('/form/create', data=payload, headers=headers)
        assert response.status_code == 302

        # correct input
        payload = {
            "form": json.dumps({
                "title": {
                    "pt": "Formulário com todos os campos",
                    "en": "Form with all fields",
                },
                "sections": [
                    {
                        "fields": [
                            {
                                "name": "text",
                                "label": {
                                    "pt": "Text",
                                    "en": "Text"
                                }, 
                                "type": "Text",
                            },
                            {
                                "name": "number",
                                "label": {
                                    "pt": "Número",
                                    "en": "Number"
                                }, 
                                "type": "Number",
                            },
                            {
                                "name": "longtext",
                                "label": {
                                    "pt": "Texto longo",
                                    "en": "Long Text"
                                }, 
                                "type": "LongText",
                            },
                            {
                                "name": "date",
                                "label": {
                                    "pt": "Data",
                                    "en": "Date"
                                }, 
                                "type": "Date",
                            },
                            {
                                "name": "file",
                                "label": {
                                    "pt": "Arquivo",
                                    "en": "File"
                                }, 
                                "type": "File",
                            },
                            {
                                "name": "radio",
                                "label": {
                                    "pt": "Radio",
                                    "en": "Radio"
                                },
                                "options": [
                                    { 
                                        "value": {
                                            "pt": "Radio 1",
                                            "en": "Radio 1"
                                        } 
                                    },
                                    { 
                                        "value": {
                                            "pt": "Radio 2",
                                            "en": "Radio 2" 
                                        }
                                    },
                                ],
                                "type": "Radio",
                            },
                            {
                                "name": "checkbox",
                                "label": {
                                    "pt": "Caixa de seleção",
                                    "en": "Checkbox"
                                },
                                "options": [
                                    { 
                                        "value": {
                                            "pt": "CheckBox 1",
                                            "en": "CheckBox 1" 
                                        }
                                    },
                                    { 
                                        "value": {
                                            "pt": "CheckBox 2",
                                            "en": "CheckBox 2" 
                                        }
                                    },
                                ],
                                "type": "CheckBox",
                            }
                        ]
                    }
                ],
                "metadata": {
                    "__message__": "entered by the system"
                }
            }),
            "_csrf_token": csrf_token
        }
        
        response = client.post('/form/create', data=payload, headers=headers)
        assert response.status_code == 200