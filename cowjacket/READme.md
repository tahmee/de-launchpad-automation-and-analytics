# Cowjacket Web Form to Jira Automation 

An automated Python-based system that bridges the gap between customer-facing web forms and internal Jira workflow management.

## Navigation / Quick Access

- [Project Overview](#project-overview)
- [Project Objectives](#project-objectives)
- [System Architecture Diagram](#system-architecture-diagram)
- [Project Structure](#project-structure)
- [Tools Used](#tools-used)
- [Project Workflow](#project-workflow)
- 
- [Key Takeaways](#key-takeaways)


##  Project Overview
At Cowjacket, customers submit support requests for phone equipment through their web form. Each request needs to be converted into a Jira Service Management ticket and assigned to internal staff for processing.

**The Problem:**  
Cowjacket's Jira instance and web form database don't communicate directly. Previously, a support staff member had to manually receive a daily CSV dump and create Jira tickets for every single request. This manual process was:
- **Slow** - 24-hour delay between submission and ticket creation
- **Error-prone** - Manual data entry leads to mistakes
- **Unscalable** - Cannot handle increasing request volumes
- **Inefficient** - Wastes valuable staff time on administrative tasks

**The Solution:**  
This automation script eliminates the manual bottleneck by connecting directly to the database and automatically creating properly formatted Jira tickets with all the necessary form data. Support requests are now processed in minutes instead of hours, allowing staff to focus on fulfilling requests and ensuring requests are seen and treated almost immediately.

## Project Objectives

### Primary Goal
Automate the creation of Jira Service Management tickets from web form submissions to eliminate manual data entry and reduce processing delays.

### Specific Objectives
1. **Eliminate Manual Work** - Remove the need for staff to manually create tickets from CSV files
2. **Reduce Processing Time** - Cut ticket creation time from 24 hours to 15 minutes
3. **Improve Accuracy** - Eliminate transcription errors through automated field mapping
4. **Enable Scalability** - Handle growing request volumes without additional staffing
5. **Prevent Duplicates** - Implement hash-based tracking to avoid creating duplicate tickets

## System Architecture Diagram

## Project Structure

```
cowjacket/
|
├── main.py                  # Main execution script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── README.md              # This file
│
├── processed_records/            # Hash records directory
│   └── processed_records.pkl   # Duplicate prevention tracking(auto-generated)
│
├── logs/                 # Log files directory
│   ├── main.log          # Execution logs
│   └── summary.log       # Daily batch summaries (auto-generated)
│   
└── venv/                 # Virtual environment (create this)
```

## Tools Used

### Programming Language
- **Python 3.8+** - Core scripting language for automation

### Key Libraries
- **jira (3.5+)** - Official Python client for Jira API interactions
- **python-dotenv** - Environment variable management for credentials
- **hashlib** (built-in) - Generating unique request identifiers
- **logging** (built-in) - Comprehensive application logging
- **datetime** (built-in) - Timestamp and date field handling
- **os** (built-in) - File system operations
### Others
- **Jira Service Management** - Ticket tracking and workflow management platform
- **Atlassian REST API** - Interface for Jira interactions
- **Git** - Version control
- **VS Code** - Code editor
- **Cron / Task Scheduler** - Automated script execution scheduling


## Project Workflow

### Script Initialisation
When the automation script runs:
1. Loads Jira credentials from environment variables
2. Loads Database credentials from environment variables
2. Connects to Jira API and authenticates
3. Loads the hash tracking file to check for previously processed requests

### Data Ingestion and Processing
- Connect to the database using the DB credentials
- Fetch records from DB
- Group fetched requests into batches for efficient processing
- Create a unique identifier for each request based on key fields
- Compare hash against processed requests to skip duplicates
- Mapped to the accurate Jira form fields, using the Jira unique field id.

#### Example of record from database
```
{
  "newusername": "Sara Curtis",
  "samplename": "Sara",
  "phonenumber": "08196712915",
  "departmentname": "Finance",
  "job": "Data Engineer",
  "emailaddress": "sara.curtis@example.com",
  "costcenter": "5540221908",
  "telephonelinesandinstallations": "New extension including new cabling and socket",
  "handsetsandheadsets": "Handset speaker phone; Mobile phone; SIM card only",
  "timeframe": "Temporary use (three months or less)",
  "dateneededby": "2025-10-28",
  "approximateendingdate": "2025-11-22",
  "Comments": "Replace faulty handset",
  "createdat": "2025-10-24"
}
```

### Ticket Creation
For each mapped request:
1. A JSON structure with all fields is created
2. POST request to Jira to create the issue
3. Retrieve ticket key (e.g., CP-154)
5. Logs success of the created ticket information otherwise logs failure

### Tracking & Logging
After processing each batch:
1. **Update Hash File** - Add new request hashes to prevent re-processing
2. **Log Results** - Record success/failure counts:
   ```
   Batch complete: 149 successful, 51 failed, 12 skipped
   ```
3. **Error Reporting** - Log detailed error messages for failed tickets

### Monitoring & Alerts
- Review logs for any failed ticket creations
- Investigate missing field mappings or validation errors
- Monitor for unusual failure rates
- Email alerts sent to admin for critical failures


### Automated Scheduling
The script `main.py` is scheduled to run every 15minutes form 7am - 5pm Monday-Friday

#### **Cron Job (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add this line to run every 15 minutes from 7 AM to 5 PM, Monday-Friday
*/15 7-17 * * * cd /path/to/cowjacket && ./venv/bin/python main.py >> logs/main.log 2>&1
```


## Key Takeaways

**What This Does**: Automatically converts web form support requests into Jira Service Management tickets, eliminating manual data entry.

**Time Saved**: Reduces maximum ticket creation delay from 24 hours to 15 minutes (automated runs every 15 minutes during business hours).

**Accuracy**: Eliminates human transcription errors through automated field mapping and validation.

**Scalability**: Handles unlimited request volumes without additional staffing - processes 200+ tickets per batch.

**Reliability**: Built-in duplicate prevention and comprehensive error logging ensure data integrity.

**Bottom Line**: Support staff can now focus on fulfilling customer requests instead of creating tickets, improving response times and service quality while reducing operational overhead.
