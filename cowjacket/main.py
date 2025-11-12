import os
import requests
import json
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

load_dotenv()

# Setup log path and directory
LOG_DIR = "logs"
LOG_FILE = "process.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
os.makedirs(LOG_DIR, exist_ok=True)


#logging config
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Jira Configuration
JIRA_URL = os.getenv('JIRA_URL') 
EMAIL = os.getenv('JIRA_EMAIL')
API_TOKEN = os.getenv('JIRA_API_TOKEN')
SERVICE_DESK_ID = os.getenv('SERVICE_DESK_ID')
REQUEST_TYPE_ID = os.getenv('REQUEST_TYPE_ID')

# Authentication
auth = (EMAIL, API_TOKEN)
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Database config
DB_CREDENTIALS=os.getenv('DB_CREDENTIALS')

# Create database engine
engine = create_engine(DB_CREDENTIALS)
Session = sessionmaker(bind=engine)

CHUNK_SIZE = 1000

def fetch_users_in_batches(batch_size=CHUNK_SIZE):
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
                query = text("""
                    SELECT *
                    FROM phonerequest
                    LIMIT :limit OFFSET :offset;
                """)
                
                result = session.execute(
                    query,
                    {"limit": batch_size, "offset": offset}
                )
                
                batch = [dict(row._mapping) for row in result]
                
                if not batch:
                    # No more records
                    break
                
                total_fetched += len(batch)
                logger.info(f"Fetched batch of {len(batch)} users (total so far: {total_fetched})")
                
                yield batch
                
                # If batch is smaller than batch_size then end loop
                if len(batch) < batch_size:
                    break
                
                offset += batch_size
                
        except Exception as e:
            logger.error(f"Failed to fetch users batch: {e}", exc_info=True)
            raise


def process_batch(batch):
    for user in batch:
        equipment_list = []
        name = user['newusername']
        job_title = user['job']
        phone = user['job']
        email = user['emailaddress']
        department = user['departmentname']
        cost_center = user['costcenter']
        installation_type = user['telephonelinesandinstallations']
        equipment = [item.strip() for item in user['handsetsandheadsets'].split(";")]
        time_usage = user['timeframe']
        ending_date = user['dateneededby']
        comments = user['Comments']

        # Set condition for users based of time_usage selection
        if time_usage == "Temporary use (three months or less)":
            time_usage = ["183"]
            approx_ending_date = user['approximateendingdate']
        elif time_usage == "Permanent use":
            time_usage = ["184"]

        # Set condition for users as this is a bullet option(one selection)
        if installation_type == "New extension including new cabling and socket":
            installation_type = ["160"]
        elif installation_type == "New extension to an existing, inactive socket":
            installation_type = ['161']
        elif installation_type == "Relocate existing to a new location ":
            installation_type = ['182']
        elif installation_type == "Convert existing extension from analogue to digital":
            installation_type = ['190']
        elif installation_type == "Relocate an existing extension to an existing inactive, socket":
            installation_type = ['191']
        elif installation_type == "Swap of telephone extensions":
            installation_type = ['192']    
        else:
            installation_type = ['0']

        # Select all applicable option (This field is multiple selection)
        for i in equipment:
            if i == "Handset speaker phone":
                equipment_list.append['164']
            if i == "Cordless headset":
                equipment_list.append['165']
            if i == "Cordless handset":
                equipment_list.append['166']
            if i == "Mobile phone":
                equipment_list.append['167']
            if i == "Smartphone":
                equipment_list.append['168']
            if i == "SIM card only":
                equipment_list.append['194']
            if i == "Other...":
                equipment_list.append['0']

        
    # Build ticket issue
    ticket_issue = {
        "serviceDeskId": SERVICE_DESK_ID,
        "requestTypeId": REQUEST_TYPE_ID,
        "requestFieldValues": {
            "summary": f"Phone equipment order - {name}",
            "description": f"Equipment request for {name} in {department}"
        },
        "form": {
            "answers": {
                # First section of form- Person making the request
                "199": {"text": name},
                "200": {"text": job_title},
                "201": {"text": phone},
                "202": {"text": email},
                "203": {"text": department},
                "204": {"text": cost_center},
                
                # Telephone lines and installations
                "157": {"choices": installation_type},
                
                # Handsets and Headsets
                "159": {"choices": equipment_list},
                
                # Time frame
                "205": {"choices": time_usage},
                "197": {"date": approx_ending_date},  
                "206": {"date": ending_date},
                
                # Comments
                "189": {"text": comments}
            }
        }
    }


# Submit the request
# url = f"{JIRA_URL}/rest/servicedeskapi/request"

# try:
#     print("Submitting request...")
#     response = requests.post(url, auth=auth, headers=headers, data=json.dumps(ticket_issue))
    
#     print(f"Status Code: {response.status_code}")
    
#     if response.status_code in [200, 201]:
#         result = response.json()
#         print(f"REQUEST CREATED SUCCESSFULLY!")
#         print("=" * 80)
#         print(f"Issue Key: {result.get('issueKey')}")
#         print(f"Issue ID: {result.get('issueId')}")
#         print(f"View your request at:")
#         print(f"{JIRA_URL}/browse/{result.get('issueKey')}")
#     else:
#         print(f" ERROR CREATING REQUEST")
#         print("=" * 80)
#         print(f"Status Code: {response.status_code}")
#         print(f"Response: {response.text}")
    
# except requests.exceptions.RequestException as e:
#     print(f"REQUEST FAILED")
#     print("=" * 80)
#     print(f"Error: {e}")
#     if 'response' in locals():
#         print(f"\nResponse text: {response.text}")
# except Exception as e:
#     print(f"UNEXPECTED ERROR")
#     print("=" * 80)
#     print(f"Error: {e}")


