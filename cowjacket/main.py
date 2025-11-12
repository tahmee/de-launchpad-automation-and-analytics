import os
import requests
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

load_dotenv()

db_credentials=os.getenv('DB_CREDENTIALS')

engine= create_engine(db_credentials)
Session = sessionmaker(bind=engine)

# with Session() as session:
#     query = """
#     SELECT *
#     FROM phonerequest
#     LIMIT 2;
#     """
#     result = session.execute(text(query))
#     rows = result.mappings().all()
#     print(rows)



# Configuration
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

# Sample data for testing
sample_data = {
    "name": "Jane Smith",
    "job_title": "Product Manager",
    "phone": "555-9876",
    "email": "jane.smith@company.com",
    "department": "Product Development",
    "cost_center": "PD-2024-001",
    "installation_type": ["160"],  # New extension including new cabling and socket
    "equipment": ["164", "165"],  # Handset speaker phone + Cordless headset
    "usage_type": "183",  # Temporary use (three months or less)
    "ending_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),  # 90 days from now
    "needed_by": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),  # 1 week from now
    "comments": "Temporary equipment needed for remote office setup during Q1 project."
}

# Build ticket issue
ticket_issue = {
    "serviceDeskId": SERVICE_DESK_ID,
    "requestTypeId": REQUEST_TYPE_ID,
    "requestFieldValues": {
        "summary": f"Phone equipment order - {sample_data['name']}",
        "description": f"Equipment request for {sample_data['name']} in {sample_data['department']}"
    },
    "form": {
        "answers": {
            # First section of form
            "199": {"text": sample_data["name"]},
            "200": {"text": sample_data["job_title"]},
            "201": {"text": sample_data["phone"]},
            "202": {"text": sample_data["email"]},
            "203": {"text": sample_data["department"]},
            "204": {"text": sample_data["cost_center"]},
            
            # Telephone lines and installations
            "157": {"choices": sample_data["installation_type"]},
            
            # Handsets and Headsets
            "159": {"choices": sample_data["equipment"]},
            
            # Time frame
            "205": {"choices": [sample_data["usage_type"]]},
            "197": {"date": sample_data["ending_date"]},  
            "206": {"date": sample_data["needed_by"]},
            
            # Comments
            "189": {"text": sample_data["comments"]}
        }
    }
}


# Submit the request
url = f"{JIRA_URL}/rest/servicedeskapi/request"

try:
    print("Submitting request...")
    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(ticket_issue))
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"REQUEST CREATED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Issue Key: {result.get('issueKey')}")
        print(f"Issue ID: {result.get('issueId')}")
        print(f"View your request at:")
        print(f"{JIRA_URL}/browse/{result.get('issueKey')}")
    else:
        print(f" ERROR CREATING REQUEST")
        print("=" * 80)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"REQUEST FAILED")
    print("=" * 80)
    print(f"Error: {e}")
    if 'response' in locals():
        print(f"\nResponse text: {response.text}")
except Exception as e:
    print(f"UNEXPECTED ERROR")
    print("=" * 80)
    print(f"Error: {e}")


