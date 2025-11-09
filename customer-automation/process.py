import os
import json
import logging
import smtplib
from sqlalchemy import create_engine, text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Initialise load_dotenv()
load_dotenv()


# Create database connection
credentials = os.getenv('DB_CREDENTIALS')
engine = create_engine(credentials)

# Connect to database
try:    
    with engine.connect() as connection:
        result = connection.execute(text('SELECT * FROM users'))
        rows = result.fetchall()
        print(f"Connection successful. Found {len(rows)} records.")

except Exception as e:
    print(f"Failed to connect: {e}")

# Set smtp credentials
sender_email=os.getenv('SENDER_EMAIL')
receiver_email=os.getenv('RECEIVER_EMAIL')
password=os.getenv('SENDER_PASSWORD')
server=os.getenv('SMTP_SERVER')
port=int(os.getenv('SMTP_PORT'))


