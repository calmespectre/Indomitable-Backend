import time
import base64
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

from .utils import get_access_token

logger = logging.getLogger(__name__)

KCB_PAYBILL_BUSINESS_NUMBER = "522533"
KCB_PAYBILL_ACCOUNT_NUMBER = "8084630"


@api_view(['POST'])
@permission_classes([AllowAny])
def stk_push(request):
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')

    if not phone_number or not amount:
        return Response(
            {'detail': 'Phone number and amount are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        access_token = get_access_token()
    except Exception as e:
        return Response({'detail': 'Failed to authenticate with Daraja'}, status=500)

    env = settings.DARAJI_ENVIRONMENT
    shortcode = settings.DARAJI_SHORTCODE
    passkey = settings.DARAJI_PASSKEY

    if env == 'sandbox':
        base_url = 'https://sandbox.safaricom.co.ke'
    else:
        base_url = 'https://api.safaricom.co.ke'

    timestamp = time.strftime('%Y%m%d%H%M%S')
    password_str = f'{shortcode}{passkey}{timestamp}'
    password = base64.b64encode(password_str.encode()).decode()

    stk_push_url = f'{base_url}/mpesa/stkpush/v1/processrequest'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://indomitable-backend-1.onrender.com/api/payments/callback/',
        'AccountReference': KCB_PAYBILL_ACCOUNT_NUMBER,
        'TransactionDesc': 'Order Payment',
    }

    try:
        response = requests.post(
            stk_push_url, json=payload, headers=headers, timeout=15
        )
        result = response.json()
        logger.info(f"STK Push Response: {result}")

        if response.status_code == 200 and result.get('ResponseCode') == '0':
            return Response({
                'checkout_request_id': result['CheckoutRequestID'],
                'merchant_request_id': result['MerchantRequestID'],
                'message': 'Payment prompt sent. Please check your phone.',
            })
        else:
            return Response({
                'detail': result.get('errorMessage', 'Failed to initiate payment'),
                'error_code': result.get('errorCode'),
                'request_id': result.get('requestId'),
            }, status=status.HTTP_400_BAD_REQUEST)

    except requests.RequestException as e:
        logger.error(f"STK Push request failed: {str(e)}")
        return Response({'detail': 'Network error during payment initiation'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def stk_callback(request):
    data = request.data
    logger.info(f"STK Callback received: {data}")

    body = data.get('Body', {})
    stkCallback = body.get('stkCallback', {})
    result_code = stkCallback.get('ResultCode')
    result_desc = stkCallback.get('ResultDesc')
    checkout_request_id = stkCallback.get('CheckoutRequestID')
    transaction_id = stkCallback.get('MpesaReceiptNumber')
    amount = stkCallback.get('Amount')
    phone = stkCallback.get('PhoneNumber')

    return Response({'ResultCode': 0, 'ResultDesc': 'Success'})


@api_view(['GET'])
@permission_classes([AllowAny])
def stk_push_status(request, checkout_request_id):
    try:
        access_token = get_access_token()
    except Exception as e:
        return Response({'detail': 'Authentication error'}, status=500)

    env = settings.DARAJI_ENVIRONMENT
    shortcode = settings.DARAJI_SHORTCODE
    passkey = settings.DARAJI_PASSKEY

    if env == 'sandbox':
        base_url = 'https://sandbox.safaricom.co.ke'
    else:
        base_url = 'https://api.safaricom.co.ke'

    timestamp = time.strftime('%Y%m%d%H%M%S')
    password_str = f'{shortcode}{passkey}{timestamp}'
    password = base64.b64encode(password_str.encode()).decode()

    query_url = f'{base_url}/mpesa/stkpushquery/v1/query'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    try:
        response = requests.post(
            query_url, json=payload, headers=headers, timeout=10)
        result = response.json()
        logger.info(f"STK Query Response: {result}")

        if response.status_code == 200:
            result_code = result.get('ResultCode')
            result_desc = result.get('ResultDesc', '')

            if result_code == '0':
                return Response({
                    'status': 'completed',
                    'message': result_desc,
                    'mpesa_receipt_number': result.get('MpesaReceiptNumber'),
                })
            elif result_code == '1037':
                return Response({
                    'status': 'failed',
                    'result_desc': result_desc or 'Payment cancelled or timed out',
                })
            else:
                return Response({
                    'status': 'pending',
                    'result_desc': result_desc or 'Transaction pending',
                })
        else:
            return Response({
                'status': 'pending',
                'detail': 'Unable to query status right now',
            }, status=502)

    except requests.RequestException as e:
        logger.error(f"STK Query error: {e}")
        return Response({'status': 'pending', 'detail': 'Network error'}, status=502)
