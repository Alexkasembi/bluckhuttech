import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta, date
from mpesa import Mpesa
from config import Config
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pymongo  # Optional for MongoDB
import pymysql  # Optional for MySQL

# Initialize the Flask application
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize M-Pesa
mpesa = Mpesa()

# Database setup (Optional - MongoDB example)
try:
    if Config.MONGODB_URI:
        mongo_client = pymongo.MongoClient(Config.MONGODB_URI)
        db = mongo_client.get_default_database()
        payments_collection = db['payments']
        contacts_collection = db['contacts']
except:
    print("MongoDB connection failed or not configured")

# OR MySQL setup (Optional)
try:
    if Config.MYSQL_HOST:
        mysql_conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
except:
    print("MySQL connection failed or not configured")

def send_email(to_email, subject, body):
    """Send email notification (optional)"""
    if not all([Config.EMAIL_SERVER, Config.EMAIL_PORT, Config.EMAIL_USERNAME, Config.EMAIL_PASSWORD]):
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(Config.EMAIL_SERVER, Config.EMAIL_PORT)
        server.starttls()
        server.login(Config.EMAIL_USERNAME, Config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')  # Automatically looks in templates/

@app.route('/pay', methods=['POST'])
def initiate_payment():
    """Handle M-Pesa payment initiation"""
    data = request.get_json()
    
    try:
        phone = data.get('phone')
        amount = data.get('amount')
        account_reference = data.get('account')
        
        if not all([phone, amount, account_reference]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Format phone number (ensure it starts with 254)
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        
        # Initiate STK push
        response = mpesa.stk_push(phone, amount, account_reference)
        
        if 'ResponseCode' in response and response['ResponseCode'] == '0':
            # Payment request successful
            payment_data = {
                'phone': phone,
                'amount': amount,
                'account_reference': account_reference,
                'request_time': datetime.now(),
                'status': 'pending',
                'mpesa_response': response
            }
            
            # Store in MongoDB (optional)
            if 'payments_collection' in globals():
                payments_collection.insert_one(payment_data)
            
            # OR Store in MySQL (optional)
            elif 'mysql_conn' in globals():
                with mysql_conn.cursor() as cursor:
                    sql = """
                    INSERT INTO payments 
                    (phone, amount, account_reference, request_time, status, mpesa_response)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        phone, amount, account_reference, 
                        datetime.now(), 'pending', json.dumps(response)
                    ))
                    mysql_conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment request initiated successfully. Check your phone to complete payment.',
                'data': response
            })
        else:
            return jsonify({
                'error': 'Payment request failed',
                'details': response.get('errorMessage', 'Unknown error')
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/callback', methods=['POST'])
def payment_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.get_json()
        print("Received callback:", data)  # For debugging
        
        # Extract relevant information from callback
        callback_data = data.get('Body', {}).get('stkCallback', {})
        result_code = callback_data.get('ResultCode')
        result_desc = callback_data.get('ResultDesc')
        checkout_request_id = callback_data.get('CheckoutRequestID')
        
        if result_code == '0':
            # Successful payment
            metadata = next(
                (item for item in callback_data.get('CallbackMetadata', {}).get('Item', []) 
                if item.get('Name') == 'MpesaReceiptNumber'),
                {}
            )
            mpesa_receipt = metadata.get('Value')
            
            # Update payment status in database (optional)
            if 'payments_collection' in globals():
                payments_collection.update_one(
                    {'mpesa_response.CheckoutRequestID': checkout_request_id},
                    {'$set': {
                        'status': 'completed',
                        'mpesa_receipt': mpesa_receipt,
                        'completion_time': datetime.now()
                    }}
                )
            
            # OR Update in MySQL (optional)
            elif 'mysql_conn' in globals():
                with mysql_conn.cursor() as cursor:
                    sql = """
                    UPDATE payments 
                    SET status = 'completed', 
                        mpesa_receipt = %s,
                        completion_time = %s
                    WHERE JSON_EXTRACT(mpesa_response, '$.CheckoutRequestID') = %s
                    """
                    cursor.execute(sql, (
                        mpesa_receipt, 
                        datetime.now(), 
                        checkout_request_id
                    ))
                    mysql_conn.commit()
            
            # Send confirmation email (optional)
            payment_record = None
            if 'payments_collection' in globals():
                payment_record = payments_collection.find_one(
                    {'mpesa_response.CheckoutRequestID': checkout_request_id}
                )
            elif 'mysql_conn' in globals():
                with mysql_conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = """
                    SELECT * FROM payments 
                    WHERE JSON_EXTRACT(mpesa_response, '$.CheckoutRequestID') = %s
                    """
                    cursor.execute(sql, (checkout_request_id,))
                    payment_record = cursor.fetchone()
            
            if payment_record and Config.EMAIL_FROM:
                email_body = f"""
                Thank you for your payment to Bluck Hut Tech Services.
                
                Payment Details:
                - Amount: KES {payment_record['amount']}
                - Receipt Number: {mpesa_receipt}
                - Account Reference: {payment_record['account_reference']}
                - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                If you have any questions, please contact us at info@bluckhuttech.com
                """
                send_email(
                    f"254{payment_record['phone'][3:]}@safaricom.co.ke",  # M-Pesa notification email
                    "Payment Confirmation - Bluck Hut Tech Services",
                    email_body
                )
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        print("Callback error:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/contact', methods=['POST'])
def handle_contact():
    """Handle contact form submissions"""
    data = request.get_json()
    
    try:
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        
        if not all([name, email, subject, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        contact_data = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'submission_time': datetime.now(),
            'status': 'unread'
        }
        
        # Store in MongoDB (optional)
        if 'contacts_collection' in globals():
            contacts_collection.insert_one(contact_data)
        
        # OR Store in MySQL (optional)
        elif 'mysql_conn' in globals():
            with mysql_conn.cursor() as cursor:
                sql = """
                INSERT INTO contacts 
                (name, email, subject, message, submission_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    name, email, subject, message, 
                    datetime.now(), 'unread'
                ))
                mysql_conn.commit()
        
        # Send confirmation email (optional)
        if Config.EMAIL_FROM:
            email_body = f"""
            Thank you for contacting Bluck Hut Tech Services.
            
            We have received your message and will get back to you soon.
            
            Message Details:
            - Name: {name}
            - Subject: {subject}
            - Message: {message}
            
            If you have any urgent inquiries, please call us at +254 712 345 678.
            """
            send_email(
                email,
                "Thank you for contacting Bluck Hut Tech Services",
                email_body
            )
            
            # Also send notification to admin
            admin_email_body = f"""
            New contact form submission:
            
            From: {name} <{email}>
            Subject: {subject}
            Message: {message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            send_email(
                Config.EMAIL_FROM,
                f"New Contact: {subject}",
                admin_email_body
            )
        
        return jsonify({
            'success': True,
            'message': 'Your message has been submitted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)