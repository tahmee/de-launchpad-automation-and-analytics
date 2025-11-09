import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# Initialise load_dotenv()
load_dotenv()

# Set smtp credentials
sender_email=os.getenv('SENDER_EMAIL')
password=os.getenv('SENDER_PASSWORD')
smtp_server=os.getenv('SMTP_SERVER')
port=int(os.getenv('SMTP_PORT'))


def database_connection():
    # Create database connection
    credentials = os.getenv('DB_CREDENTIALS')
    engine = create_engine(credentials)

    # Create session
    Session =sessionmaker(bind=engine)
    session = Session()

    # Connect to database
    try:    
        with engine.connect() as connection:
            result = connection.execute(text('SELECT * FROM users'))
            rows = result.fetchall()
            print(f"Connection successful. Found {len(rows)} records.")

    except Exception as e:
        print(f"Failed to connect: {e}")

    query = text("""
        SELECT first_name,
            email_address
        FROM users
        WHERE subscription_status = 'active'
            AND email_frequency = 'daily'
        ORDER BY first_name;
    """)
    result = session.execute(query)
    customers = [dict(row._mapping) for row in result]

    session.close()

    return customers

def send_email(user_name, user_email):
    # Email settings
    sender_name = "MindFuel"
    subject = "Daily Inspiration from MindFuel"

    # Dynamic content - Change these values
    recipient_name = user_name
    daily_quote = "The only way to do great work is to love what you do."
    quote_author = "Steve Jobs"

    # HTML email template
    html_body = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MindFuel Email</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; text-align: center;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: bold; color: #333333;">MINDFUEL</h1>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 20px 40px;">
                                <h2 style="margin: 0 0 20px 0; font-size: 22px; font-weight: bold; color: #333333; text-align: center;">
                                    STRENGTH STARTS<br>FROM THE MIND
                                </h2>
                                
                                <p style="margin: 0 0 30px 0; font-size: 16px; color: #666666; text-align: center; font-weight: bold;">
                                    DAILY QUOTE TO KEEP YOU GOING
                                </p>
                                
                                <p style="margin: 0 0 20px 0; font-size: 15px; color: #333333; line-height: 1.6;">
                                    Hi {name},
                                </p>
                                
                                <p style="margin: 0 0 30px 0; font-size: 15px; color: #333333; line-height: 1.6;">
                                    Here's something to get your day started.
                                </p>
                                
                                <div style="background-color: #f8f8f8; padding: 30px; margin: 0 0 20px 0; border-left: 4px solid #4CAF50; border-radius: 4px;">
                                    <p style="margin: 0 0 15px 0; font-size: 18px; color: #333333; line-height: 1.8; font-style: italic;">
                                        {quote}
                                    </p>
                                    <p style="margin: 0; font-size: 14px; color: #666666; text-align: right;">
                                        - {author}
                                    </p>
                                </div>
                                
                                <p style="margin: 30px 0 0 0; font-size: 15px; color: #333333; line-height: 1.6;">
                                    Best Regards,<br>
                                    <strong>MindFuel</strong>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f8f8f8; border-top: 1px solid #e0e0e0;">
                                <p style="margin: 0 0 10px 0; font-size: 16px; color: #333333; font-weight: bold;">
                                    MindFuel
                                </p>
                                <p style="margin: 0 0 15px 0; font-size: 13px; color: #666666; line-height: 1.6;">
                                    Suite 123, 123 Anywhere Street,<br>
                                    Any City, ST 12345
                                </p>
                                <p style="margin: 0; font-size: 12px; color: #999999; line-height: 1.6;">
                                    You're receiving this email because you signed up for updates from MindFuel.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """.format(name=recipient_name, quote=daily_quote, author=quote_author)

    # Plain text version
    text_body = f"""
    MINDFUEL
    STRENGTH STARTS FROM THE MIND
    DAILY QUOTE TO KEEP YOU GOING

    Hi {recipient_name},

    Here's something to get your day started.

    "{daily_quote}"
    - {quote_author}

    Best Regards,
    MindFuel

    MindFuel
    Suite 123, 123 Anywhere Street,
    Any City, ST 12345

    You're receiving this email because you signed up for updates from MindFuel.
    """

    # Create message
    message = MIMEMultipart('related')
    message['From'] = formataddr((sender_name, sender_email))
    message['To'] = user_email
    message['Subject'] = subject

    # Alternative container
    msg_alternative = MIMEMultipart('alternative')
    message.attach(msg_alternative)

    # Attach text and HTML
    msg_alternative.attach(MIMEText(text_body, 'plain'))
    msg_alternative.attach(MIMEText(html_body, 'html'))


    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        print('Email sent successfully! 🎉')
    except Exception as e:
        print(f'Error sending email: {e}')


def get_quote(filename):
    with open(filename, 'r') as file:
        file.read()
    return file

file_path =

users = database_connection()
success_count = 0
failure_count = 0


for user in users:
    try:
        name = user['first_name']
        email = user['email_address']
        send_email(name, email)
        print(f"Email sent successfully to {name}, {email} ")
    except Exception as e:
        print(f"Failed to send email to {user.get('first_name', 'Unknown')}: {e}")
        failure_count += 1