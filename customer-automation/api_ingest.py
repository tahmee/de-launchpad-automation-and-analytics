# Import required packages
import logging
import requests
import json
import os
from dotenv import load_dotenv

# Setup log and output file path
LOG_DIR = "logs"
LOG_FILE = "api_ingest.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
OUTPUT_DIR = "api_data"
OUTPUT_FILE = "quote_data.json"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILE)


# Setup logging config
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Initialize logging
logger = logging.getLogger(__name__)

# Call load_dotenv
load_dotenv()

# Assign Zenquotes(quote only) API endpoint to variable zq_api
zq_api = os.getenv("API_URL")

# Set constant API timeout
API_TIMEOUT = 10

# Define function to create directories
def setup_directories():
    """Create directories if they don't exist."""
    # Create logs directory
    os.makedirs(LOG_DIR, exist_ok=True)
       
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# Define function to connect to api and fetch data
def fetch_api_data(url):
    """Connects to API, fetches and parse JSON data.
    Args:
        url (str): The API url to fetch the data from.
    
    Returns: 
        list[dict] | None: A list of dictionaries containing the API data or None if requests fails
    
    Raises:
        Logs errors for connection issues, timeout or parsing failure.
    """
    try:
        logger.info(f"Attempting to fetch data from {url}")
        response = requests.get(url, timeout=API_TIMEOUT)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info("Data successfully retrieved and parsed into JSON")
            return data
        else:
            logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out for {url}")
        return None
    
    except requests.exceptions.ConnectionError:
        logger.error(f"A connection error occurred for {url}")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
    
    except ValueError as e:
        logger.error(f"Failed to parse data into JSON: {str(e)}")
        return None
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return None


# Define function to filter data and save only required key-value pairs
def filter_data(data):
    """Takes parsed JSON data, filters for required key-value pairs and saves into new list.
    
    Args:
        data (list[dict]): API response with 'a' (author) and 'q' (quote) keys.
    
    Returns:
        list[dict]: Filtered quotes with 'author' and 'quote' keys.

    """
    if not data:
        logger.warning("No data provided to filter")
        return None
    
    logger.info(f"Starting data filtering. {len(data)} records to process")
    selected_data = []
    skipped_records = 0
    
    # Loop through argument(list of dict)
    for item in data:
        try:
            author = item['a']
            quote = item['q']

            # Create new dictionary to store selected key-value pairs(just author and quote)
            quote_dict = {
                'author': author,
                'quote': quote
            }
            # Append new dict to list 'selected_data' defined at top of function
            selected_data.append(quote_dict)

        except KeyError as e:
            logger.warning(f"Missing expected key in item: {e}. Skipping item.")
            skipped_records += 1
            continue  # Skip malformed items, process the rest
        except Exception as e:
            logger.error(f"Unexpected error processing item: {e}")
    logger.info(f"Successfully filtered {len(selected_data)} records. Skipped {skipped_records} records")
    return selected_data

# Define function to save filtered data into a .json file
def save_to_json(data, filename=OUTPUT_PATH):
    """
    Saves filtered data to a JSON file.
    
    Args:
        data (list[dict]): List of quote dictionaries with 'author' and 'quote' keys.
        filename (str, optional): Output file path. Defaults to 'quote_data.json'.
    
    Note:
        Overwrites existing files. Logs success/failure.
    """
    logger.info(f"Attempting to save data to {filename}")
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            logger.info(f"Filtered data successfully saved to {filename}")
    except PermissionError:
        logger.error(f"Permission denied: Cannot write to {filename}")
    except OSError as e:
        logger.error(f"OS error while saving file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while trying to save to JSON file: {e}", exc_info=True)


if __name__ == "__main__":
    #Fetch quotes from Zenquotes API, filter to author/quote pairs, and save locally.
    try:
        setup_directories()
        logger.info("BEGIN------------------------------")

        api_data = fetch_api_data(zq_api) 
        if api_data:  # Only proceed if data was successfully fetched
            new_data = filter_data(api_data) 
            if new_data:
                save_to_json(new_data) 
                print(f"Successfully saved {len(new_data)} quotes to {OUTPUT_PATH}")
                logger.info("Script executed successfully")
            else:
                logger.warning("No data to save after filtering")
        else:
            logger.error("Failed to fetch data from API")

    except Exception as e:
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)
        