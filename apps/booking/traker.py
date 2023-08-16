import requests

from constance import config


LOGIN = 'https://portal.trackme.lk/api/v1/login'


def login():
    response = requests.post(
        LOGIN,
        data={
            "username": config.TRACKER_USERNAME,
            "password": config.TRACKER_PASSWORD,
        },
        verify=False,
        headers={"apiKey": config.TRACKER_APIKEY}
    )
    return response.json().get("")
