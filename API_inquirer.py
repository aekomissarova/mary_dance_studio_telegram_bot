import requests


def login_in_api(phone_number, password):
    url_login = 'url'

    payload_json = {
        "client_id": phone_number,
        "client_secret": password,
        "grant_type": "client_credentials",
        "scope": "userinfo cloud file node",
        "response": "",
        "viewer_id": ""
    }
    login = requests.post(url_login, json=payload_json)
    token = login.text[52:84]
    return token


def get_events(token):
    url_events = 'url'
    events = requests.post(url_events, json={"_token": token, "weekday": 1})
    return events.text
