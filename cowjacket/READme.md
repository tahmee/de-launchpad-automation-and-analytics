# MindFuel - Daily Quote Email Automation System

## Navigation / Quick Access

- [Overview](#Overview)
- [Features](#Features)
- [System Architecture Diagram](#System-Architecture-Diagram)
- [Prerequisites](#prerequisites)
- [Reproducibility Guide](#reproducibility-guide)


## Overview
This project is a python based email automation system for MindFuel (a fictional mental health wellness startup). It fetches daily inspirational quotes from [ZenQuotes](https://zenquotes.io/) and delivers them to subscribers gotten from a database via personalised emails. This system supports both daily and weekly subscription frequencies.

## Features
MindFuel is a three-stage automation system designed to:
1. **Quote Ingestion** (`api_ingest.py`): Fetch daily inspirational quotes from the [ZenQuotes API](https://docs.zenquotes.io/zenquotes-documentation/) and cache them locally.
2. **User Retrieval** (`process.py`): Fetch users records from a database based off their subscription frequency (i.e daily/weekly).
3. **Email Distribution** (`process.py`): Sends personalised emails to subscribers with the day's quote, supporting both daily and weekly delivery schedules.

## System Architecture Diagram


## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL or any local/cloud based database
- SMTP server access (e.g., Gmail, SendGrid)
- Internet connection for API access


## 🔬 Reproducibility Guide

This section provides step-by-step instructions to reproduce the exact environment and run the system from scratch

### Installation

#### 1. Clone the Repository

```bash
git clone git@github.com:tahmee/de-launchpad-automation-and-analytics.git
cd customer-automation/
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

#### 1. Gmail Setup (If Using Gmail)
1. Enable 2-Factor Authentication on your Google account.
2. Generate an App Password:
   - Go to your [Google Account](https://myaccount.google.com/) → Security
   - Select "2-Step Verification"
   - At the bottom, select "App passwords"
   - Generate a password for "Mail" (you can give it any name of your choice)
3. Use this App Password as `SENDER_PASSWORD` in your `.env` file

#### 2. Database Setup

Create the required database table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    email_address VARCHAR(255) NOT NULL UNIQUE,
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active',
    email_frequency VARCHAR(10) NOT NULL CHECK (email_frequency IN ('daily', 'weekly')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_subscription_status ON users(subscription_status);
CREATE INDEX idx_email_frequency ON users(email_frequency);

-- Sample data insertion
INSERT INTO users (first_name, email_address, subscription_status, email_frequency)
VALUES 
    ('John', 'john@example.com', 'active', 'daily'),
    ('Jane', 'jane@example.com', 'active', 'weekly'),
    ('Bob', 'bob@example.com', 'active', 'daily');
```

#### 3. Environment Variables Setup

Create a `.env` file in the project root directory:

```bash
# API Configuration
API_URL=https://zenquotes.io/api/today

# Database Configuration
DB_CREDENTIALS=postgresql://username:password@host:port/database_name
# Example: postgresql://admin:mypassword@localhost:5432/mindfuel_db

# File Paths
FILE_PATH=api_data/quote_data.json

# SMTP Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password-here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_TIMEOUT=30

# Alert Configuration
ALERT_EMAIL=admin@yourdomain.com
SEND_ALERTS=true
```


#### 4. Directory Structure Creation

The scripts will automatically create necessary directories, but you can also create them manually:

```bash
mkdir -p logs api_data
```
