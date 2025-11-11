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
from datetime import datetime
import time

# Initialise load_dotenv()
load_dotenv()

# Setup log path and directory
LOG_DIR = "logs"
LOG_FILE = "process.log"
SUMMARY_LOG_FILE = "summary.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
SUMMARY_LOG_PATH = os.path.join(LOG_DIR, SUMMARY_LOG_FILE)
os.makedirs(LOG_DIR, exist_ok=True)


#logging config
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create logger for summary stats
summary_logger = logging.getLogger('summary_text')
summary_logger.setLevel(logging.INFO)
summary_handler = logging.FileHandler(SUMMARY_LOG_PATH)
summary_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
summary_logger.addHandler(summary_handler)
summary_logger.propagate = False 

# SMTP credentials/ DB config
SENDER_EMAIL=os.getenv('SENDER_EMAIL')
SENDER_PASSWORD=os.getenv('SENDER_PASSWORD')
SMTP_SERVER=os.getenv('SMTP_SERVER')
SMTP_PORT=int(os.getenv('SMTP_PORT'))
SMTP_TIMEOUT=int(os.getenv('SMTP_TIMEOUT'))
# Set database credentials and file path
DB_CREDENTIALS=os.getenv('DB_CREDENTIALS')
FILE_PATH=os.getenv('FILE_PATH') # Path to quotes file

# Alert email configuration
ALERT_EMAIL=os.getenv('ALERT_EMAIL') 
SEND_ALERTS=os.getenv('SEND_ALERTS').lower() == 'true'

# Email configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds 
RATE_LIMIT_DELAY = 0.1  # seconds between emails (10 emails/second)

CHUNK_SIZE = 1000

# Create database engine
try:
    logger.info("=" * 30)
    logger.info("BEGIN EMAIL AUTOMATION SCRIPT")
    logger.info("=" * 30)
    engine = create_engine(DB_CREDENTIALS)
    Session = sessionmaker(bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    engine = None
    Session = None
    raise


def fetch_users_in_batches(email_frequency, batch_size=CHUNK_SIZE):
    """
    Fetch users in batches from database.
    """
    if not Session:
        raise Exception("Database session not initialised")
    
    offset = 0
    total_fetched = 0
    
    while True:
        try:
            with Session() as session:
                logger.info(f"Database connection successful.")
                query = text("""
                    SELECT first_name, email_address
                    FROM users
                    WHERE subscription_status = 'active'
                        AND email_frequency = :frequency
                    ORDER BY first_name
                    LIMIT :limit OFFSET :offset;
                """)
                
                result = session.execute(
                    query,
                    {"frequency": email_frequency, "limit": batch_size, "offset": offset}
                )
                
                batch = [dict(row._mapping) for row in result]
                
                if not batch:
                    # No more records
                    break
                
                total_fetched += len(batch)
                logger.info(f"Fetched batch of {len(batch)} {email_frequency} users (total so far: {total_fetched})")
                
                yield batch
                
                # If batch is smaller than batch_size then end loop
                if len(batch) < batch_size:
                    break
                
                offset += batch_size
                
        except Exception as e:
            logger.error(f"Failed to fetch users batch: {e}", exc_info=True)
            raise



def email_template(recipient_name, quote, author):
    """Generate HTML and plain text email templates."""
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
    """.format(name=recipient_name, quote=quote, author=author)

    # Plain text version
    text_body = f"""
    MINDFUEL
    STRENGTH STARTS FROM THE MIND
    DAILY QUOTE TO KEEP YOU GOING

    Hi {recipient_name},

    Here's something to get your day started.

    "{quote}"
    - {author}

    Best Regards,
    MindFuel

    MindFuel
    Suite 123, 123 Anywhere Street,
    Any City, ST 12345

    You're receiving this email because you signed up for updates from MindFuel.
    """
    return html_body, text_body


def send_email_config(user_name, user_email, quote, author, sender_name='MindFuel', subject = "Inspiration from MindFuel", max_retries=MAX_RETRIES):
    """Send email with max retry in place."""
    for attempt in range(1, max_retries + 1):
        try:
            # Create message
            message = MIMEMultipart('related')
            message['From'] = formataddr((sender_name, SENDER_EMAIL))
            message['To'] = user_email
            message['Subject'] = subject

            # Alternative container
            msg_alternative = MIMEMultipart('alternative')
            message.attach(msg_alternative)

            html_body, text_body = email_template(user_name, quote=quote, author=author)
            # Attach text and HTML
            msg_alternative.attach(MIMEText(text_body, 'plain'))
            msg_alternative.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(message)
             
                logger.info(f'Email sent successfully {user_name}, {user_email} on attempt {attempt}!')
            return True
        except smtplib.SMTPException as e:
            logger.warning(f'SMTP error sending to {user_email} (attempt {attempt}/{max_retries}): {e}')
            if attempt < max_retries:
                sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(sleep_time)
            else:
                logger.error(f'Failed to send email to {user_email} after {max_retries} attempts')
                raise
            
        except Exception as e:
            logger.error(f'Unexpected error sending to {user_email} (attempt {attempt}/{max_retries}): {e}')
            if attempt < max_retries:
                sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(sleep_time)   
            else:
                logger.error(f'Failed to send email to {user_email} after {max_retries} attempts')
                raise
        
    return False


def get_quote(filename):
    """Load quote from JSON file."""
    with open(filename, 'r', encoding='utf-8') as file:
        quote = json.load(file)
        return quote['quote'], quote['author']
    

def process_user_batch(batch, quote, author, stats):
    
    for user in batch:
        name = user['first_name']
        email = user['email_address']

        stats['records_processed'] += 1
        try: 
            success = send_email_config(name, email, quote, author)
            if success:
                stats['emails_sent'] += 1
            else:
                stats['failed'] += 1           
           
        except Exception as e:
            stats['failed'] += 1 
            logger.error(f"Failed to send email to {name} ({email}): {e}")
            
     # Update every 100 emails progress
        if stats['records_processed'] % 100 == 0:
            logger.info(f"Progress: {stats['records_processed']} emails processed.")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)   


def generate_summary(stats, day_name, duration, success=True):
    """Generate summary text for alert email."""
    total = stats['records_processed']
    success_rate = (stats['emails_sent'] / total * 100) if total > 0 else 0
    
    summary = f"""
        MindFuel Email Automation Report
        {'-'*20}
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Day: {day_name}
        Status: {'SUCCESS' if success else 'FAILED'}

        STATISTICS:
        -----------
        Total processed: {total}
        Successfully sent: {stats['emails_sent']}
        Failed: {stats['failed']}
        Success rate: {success_rate:.2f}%

        BREAKDOWN:
        ----------
        Daily subscribers: {stats['daily']}
        Weekly subscribers: {stats['weekly']}

        PERFORMANCE:
        ------------
        Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)
        Throughput: {stats['emails_sent'] / duration:.2f} emails/second
        """
    return summary


def log_final_summary(stats, day_name, duration):
    """Log final summary to file."""
    summary_logger.info("=" * 30)
    summary_logger.info(f"EMAIL STATISTICS SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_logger.info(f"Day: {day_name}")
    summary_logger.info(f"Total processed: {stats['records_processed']}")
    summary_logger.info(f"Daily subscribers: {stats['daily']}")
    summary_logger.info(f"Weekly subscribers: {stats['weekly']}")
    summary_logger.info(f"Successfully sent: {stats['emails_sent']}")
    summary_logger.info(f"Failed: {stats['failed']}")
    
    if stats['records_processed'] > 0:
        success_rate = (stats['emails_sent'] / stats['records_processed']) * 100
        summary_logger.info(f"Success rate: {success_rate:.2f}%")
    
    summary_logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    
    if duration > 0:
        throughput = stats['emails_sent'] / duration
        summary_logger.info(f"Throughput: {throughput:.2f} emails/second")
    
    summary_logger.info("=" * 30)


def send_alert_email(summary_text, subject="MindFuel Email Automation Summary"):
    """Send alert email with statistics summary to admin."""
    if not ALERT_EMAIL:
        logger.warning("ALERT_EMAIL not configured, skipping alert email")
        return False
        
    try:
        # Create HTML version of summary
        html_summary = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Courier New', monospace; background-color: #f4f4f4; padding: 20px; }}
                .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
                h2 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
                pre {{ background-color: #f8f8f8; padding: 15px; border-left: 4px solid #4CAF50; overflow-x: auto; font-size: 13px; line-height: 1.6; }}
                .success {{ color: #4CAF50; font-weight: bold; }}
                .warning {{ color: #ff9800; font-weight: bold; }}
                .error {{ color: #f44336; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>MindFuel Email Automation Report</h2>
                <pre>{summary_text}</pre>
            </div>
        </body>
        </html>
        """
        
        message = MIMEMultipart('alternative')
        message['From'] = formataddr(('MindFuel Alert System', SENDER_EMAIL))
        message['To'] = ALERT_EMAIL
        message['Subject'] = subject
        
        message.attach(MIMEText(summary_text, 'plain'))
        message.attach(MIMEText(html_summary, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Alert email sent successfully to {ALERT_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}", exc_info=True)
        return False


def main():
    """Main execution function."""
    start_time = datetime.now()
    if not FILE_PATH:
        logger.error("FILE_PATH environment variable not set")
        return 1
    
    if not all([SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        logger.error("Missing required email configuration")
        return 1
    else:
        logger.info("Connection to SMTP server sucessful.")
    
    if not DB_CREDENTIALS:
        logger.error("DB_CREDENTIALS not set")
        return 1
    
    if not engine or not Session:
        logger.error("Database engine initialization failed")
        return 1
    
    # Get the quote for today
    try:
        quote, author = get_quote(FILE_PATH)
        logger.info(f"Quote loaded successfully: '{quote[:30]}...' by {author}")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load quote: {e}")
        return 1
    
    stats = {
        'records_processed': 0,
        'emails_sent': 0,
        'failed': 0,
        'daily': 0,
        'weekly': 0
    }
    # Get day to filter for weekly subscribers
    day_name = datetime.now().strftime("%A")
    try:
        # process daily users in batches
        logger.info("Attempting to fetch daily subscribers")
        for batch in fetch_users_in_batches('daily', CHUNK_SIZE):
            process_user_batch(batch, quote, author, stats)
            stats['daily'] += len(batch)
        logger.info(f"Completed daily subscribers: {stats['daily']} users processed.")
        
        # Process weekly users only on Monday
        if day_name == 'Monday':
            logger.info("Attempting to fetch weekly subscribers")
            for batch in fetch_users_in_batches('weekly', CHUNK_SIZE):
                process_user_batch(batch, quote, author, stats)
                stats['weekly'] += len(batch)
            logger.info(f"Completed weekly subscribers: {stats['weekly']} users processed")
        else:
            logger.info("Skipped weekly subscribers it's not Monday")
 
    except Exception as e:
        logger.error(f"Critical error during batch processing: {e}", exc_info=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = generate_summary(stats, day_name, duration, success=False)
        send_alert_email(summary, subject=" MindFuel Email Automation Failed")
        
        return 1
    
    # Calculate final stats 
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    
    # Log final summary
    summary_text = log_final_summary(stats, day_name, duration)
    summary_logger.info(summary_text)

    # Send alert email with summary
    summary = generate_summary(stats, day_name, duration, success=True)
    send_alert_email(summary)
    
    # Return 0 for success, 1 if there were failures
    return 0 if stats['failed'] == 0 else 1


    

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"Script completed with exit code: {exit_code}")
        exit(exit_code)
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}", exc_info=True)
        exit(1)