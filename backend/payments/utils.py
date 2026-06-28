import requests
from django.conf import settings
import base64


def get_access_token():
    env = settings.DARAJI_ENVIRONMENT
    consumer_key = settings.DARAJI_CONSUMER_KEY
    consumer_secret = settings.DARAJI_CONSUMER_SECRET

    if env == 'sandbox':
        base_url = 'https://sandbox.safaricom.co.ke'
    else:
        base_url = 'https://api.safaricom.co.ke'

    auth_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(auth_url, auth=(consumer_key, consumer_secret))
    result = response.json()

    if response.status_code == 200:
        return result.get('access_token')
    raise Exception(f"Failed to get access token: {result}")
