import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # M-Pesa Configuration
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
    BUSINESS_SHORTCODE = os.getenv('BUSINESS_SHORTCODE')
    
    # Email Configuration
    EMAIL_SERVER = os.getenv('EMAIL_SERVER')
    EMAIL_PORT = os.getenv('EMAIL_PORT')
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    
    # Database Configuration (MongoDB)
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # OR MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')