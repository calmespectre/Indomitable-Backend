import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_access_token():
    env = settings.DARAJI_ENVIRONMENT
    consumer_key = settings.DARAJI_CONSUMER_KEY
    consumer_secret = settings.DARAJI_CONSUMER_SECRET

    if env == 'sandbox':
        base_url = 'https://sandbox.safaricom.co.ke'
    else:
        base_url = 'https://api.safaricom.co.ke'

    auth_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'

    try:
        response = requests.get(auth_url, auth=(
            consumer_key, consumer_secret), timeout=15)
        result = response.json()
        logger.info(f"Auth response: {result}")

        if response.status_code == 200:
            return result.get('access_token')
        else:
            error_msg = result.get(
                'errorMessage', result.get('error', 'Unknown error'))
            logger.error(
                f"Authentication failed: {error_msg} (Status: {response.status_code})")
            raise Exception(f"Daraja authentication failed: {error_msg}")
    except requests.RequestException as e:
        logger.error(f"Network error during auth: {str(e)}")
        raise Exception("Could not connect to Safaricom API. Check network.")
