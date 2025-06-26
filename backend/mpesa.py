from datetime import timedelta

def my_function():
    delta = timedelta(days=1)
import requests
import base64
from datetime import datetime
import json
from config import Config
class Mpesa:
    def __init__(self):
        self.consumer_key = Config.MPESA_CONSUMER_KEY
        self.consumer_secret = Config.MPESA_CONSUMER_SECRET
        self.passkey = Config.MPESA_PASSKEY
        self.shortcode = Config.MPESA_SHORTCODE
        self.callback_url = Config.MPESA_CALLBACK_URL
        self.business_shortcode = Config.BUSINESS_SHORTCODE
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get M-Pesa OAuth access token"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
            
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        auth = (self.consumer_key, self.consumer_secret)
        response = requests.get(url, auth=auth)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            # Token expires in 1 hour (3600 seconds)
            self.token_expiry = datetime.now() + timedelta(seconds=3500)
            return self.access_token
        else:
            raise Exception("Failed to get access token")
    
    def stk_push(self, phone, amount, account_reference):
        """Initiate STK push payment request"""
        access_token = self.get_access_token()
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.business_shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "Payment for services"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()