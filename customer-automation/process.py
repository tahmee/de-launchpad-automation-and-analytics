import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

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