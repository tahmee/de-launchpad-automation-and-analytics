import os
import requests
import json
import logging
import hashlib
import pickle
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

# Set directory path for tracking processed records
RECORD_DIR = "record"
RECORD_FILE = "processed_records.pkl"
RECORD_PATH = os.path.join(RECORD_DIR, RECORD_FILE)
os.makedirs(RECORD_DIR, exist_ok=True)

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

# Time window for fetching records (fetch last 24 hours)
TRACK_HOURS = 24

def generate_hash_record(user):
    """Generate a unique hasd for each record based on combination of several fields"""

    hash_string = f"{user['newusername']}|{user['emailaddress']}|{user['phonenumber']}|{user['createdat']}|{user['dateneededby']}|{user['telephonelinesandinstallations']}|{user['handsetsandheadsets']}"
    return hashlib.sha256(hash_string.encode()).hexdigest()


def load_processed_records():
    """
    Load the set of already processed record hashes from state file.
    """
    if os.path.exists(RECORD_PATH):
        try:
            with open(RECORD_PATH, 'rb') as file:
                data = pickle.load(file)
                logger.info(f"Loaded {len(data['hashes'])} previously processed records.")
                return data
        except Exception as e:
            logger.warning(f"Could not load record file: {e}. Starting fresh.")
            return {"hashes": set(), "last_run": None}
    return {"hashes": set(), "last_run": None}


def save_processed_records(processed_data):
    """
    Save the set of processed record hashes to state file.
    """
    try:
        processed_data["last_run"] = datetime.now().isoformat()
        with open(RECORD_PATH, 'wb') as file:
            pickle.dump(processed_data, file)
        logger.info(f"Saved state with {len(processed_data['hashes'])} processed records")
    except Exception as e:
        logger.error(f"Failed to save state file: {e}", exc_info=True)


def fetch_users_in_batches(batch_size=CHUNK_SIZE):
    """
    Fetch users in batches from database.
    """
    if not Session:
        raise Exception("Database session not initialised")
    
    # Calculate the hours 
    #time_tracker = (datetime.now() - timedelta(hours=hours)).date()

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


def process_batch(batch, processed_records):
    """Process a batch of users and create Jira tickets for each user.
        Skips records already processed
    """

    success = 0
    failed = 0
    skipped = 0
    new_hash = set()

    for user in batch:
        try:
            # Generate hash for new record
            hash_record = generate_hash_record(user)

            # Skip if already processed
            if hash_record in processed_records:
                logger.debug(f"Skipping already processed record for {user['newusername']}")
                skipped += 1
                continue

            # Extract user data
            name = user['newusername']
            job_title = user['job']
            phone = user['phonenumber']
            email = user['emailaddress']
            department = user['departmentname']
            cost_center = user['costcenter']
            installation_type = user['telephonelinesandinstallations']
            equipment = [item.strip() for item in user['handsetsandheadsets'].split(";")]
            time_usage_raw = user['timeframe']
            ending_date = user['dateneededby']
            comments = user['Comments']

            # Initialise variables
            approx_ending_date = None

            # Set condition for users based of time_usage selection
            if time_usage_raw == "Temporary use (three months or less)":
                time_usage = ["183"]
                approx_ending_date = user['approximateendingdate']
            elif time_usage_raw == "Permanent use":
                time_usage = ["184"]


         # Process installation type
            installation_mapping = {
                "New extension including new cabling and socket": ["160"],
                "New extension to an existing, inactive socket": ["161"],
                "Relocate existing to a new location": ["182"],
                "Convert existing extension from analogue to digital": ["190"],
                "Relocate an existing extension to an existing inactive, socket": ["191"],
                "Swap of telephone extensions": ["192"],
                "Other... (multi-line hunt group setup)": ["0"]
            }
            installation_type_cd = installation_mapping[installation_type]
            
            # Process equipment
            equipment_list = []
            equipment_mapping = {
                "Handset speaker phone": "164",
                "Cordless headset": "165",
                "Cordless handset": "166",
                "Mobile phone": "167",
                "Smartphone": "168",
                "SIM card only": "194",
                "Other...": "0"
            }
            
            for item in equipment:
                if item in equipment_mapping:
                    equipment_list.append(equipment_mapping[item])
        
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
                        "157": {"choices": installation_type_cd},
                        
                        # Handsets and Headsets
                        "159": {"choices": equipment_list},
                        
                        # Time frame
                        "205": {"choices": time_usage},  
                        "206": {"date": ending_date},
                        
                        # Comments
                        "189": {"text": comments}
                    }
                }
            }


            # Add approx_ending_date only if it exists
            if approx_ending_date:
                ticket_issue["form"]["answers"]["197"] = {"date": approx_ending_date}


            #Submit the request
            url = f"{JIRA_URL}/rest/servicedeskapi/request"
            response = requests.post(
                url, 
                auth=auth, 
                headers=headers, 
                data=json.dumps(ticket_issue),
                timeout=30  
            )

            if response.status_code in [200, 201]:
                result = response.json()
                issue_key = result['issueKey']
                logger.info(f"Sucessfully created ticket {issue_key} for {name}")
                success += 1
                # Add record to records processed
                new_hash.add(hash_record)
            else:
                logger.error(f"Failed to create ticket for {name}: Status {response.status_code} - {response.text}")
                failed += 1

        except KeyError as e:
            # Handle missing fields
            logger.error(f"Missing required field for user {e}", exc_info=True)
            failed += 1
        
        except requests.exceptions.RequestException as e:
            # Handle API request errors
            logger.error(f"API request failed for {user['newusername']}: {e}", exc_info=True)
            failed += 1
            
        except Exception as e:
            # Handle any other errors
            logger.error(f"Unexpected error processing user {user['newusername']}: {e}", exc_info=True)
            failed += 1

    logger.info(f"Batch complete: {success} successful, {failed} failed")
    return success, failed, skipped, new_hash   


def main():
    """Main execution function."""
    logger.info("=" * 30)
    logger.info("STARTING JIRA TICKET CREATION PROCESS")
    logger.info("=" * 30)
    
    # Load previously processed records
    records = load_processed_records()
    processed_hash = records['hashes']

    if records['last_run']:
        logger.info(f"Last successful run: {records['last_run']}")

    total_success = 0
    total_failed = 0
    total_skipped = 0
    new_hashs = set()
    
    try:
        for batch in fetch_users_in_batches():
            success, failed, skipped, new_hash = process_batch(batch, processed_hash)
            total_success += success
            total_failed += failed
            total_skipped += skipped
            new_hashs.update(new_hash)

            # Update file with newly processed records
            records['hashes'].update(new_hashs)
            save_processed_records(records)

        logger.info("=" * 10)
        logger.info(f"Process complete!")
        logger.info(f"Total successful: {total_success}")
        logger.info(f"Total failed: {total_failed}")
        logger.info(f"Total skipped: {total_skipped}")
        logger.info(f"New records processed: {len(new_hashs)}")
        
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()