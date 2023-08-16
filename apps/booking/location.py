from typing import Optional
import requests

import googlemaps
from constance import config


def get_location():
    response = requests.get(
        'https://track.trackerway.com/api/api.php'
        '?api=user'
        '&ver=1.0'
        f'&key={config.GEO_API_KEY}'
        '&cmd=OBJECT_GET_LOCATIONS,"*"',
        verify=False
    )
    try:
        content = response.json().get(config.GEO_ID)
        return content.get("lat"), content.get("lng")
    except Exception as e:
        print(e)
        return None


def get_time_to(post_code):
    client = googlemaps.Client(key=config.GOOGLE_API_KEY)
    location = get_location()
    if not location:
        return
    lat, lng = location
    try:
        response = client.distance_matrix(**{
            'units': 'metric',
            'mode': 'driving',
            'origins': [{"lat": lat, "lng": lng}],
            'destinations': [post_code],
        })
    except Exception:
        return
    if response.get('status', 'failed') != 'OK':
        return
    duration = response.get("rows", [])[0]
    durations = {
        element.get('duration').get('value'): element.get("duration").get("text")
        for row in response.get('rows')
        for element in row.get('elements')
    }
    min_duration = min(durations.keys())
    return round(min_duration / 60), durations.get(min_duration)
