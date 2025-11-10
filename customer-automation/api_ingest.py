import logging
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Setup directories
LOG_DIR = "logs"
LOG_FILE = "api_ingest.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
OUTPUT_DIR = "api_data"
OUTPUT_FILE = "quote_data.json"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# logging config
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# load enviroment
load_dotenv()

# Assign ZenQuotes API endpoint to variable zq_api
zq_today_api = os.getenv("API_URL")

# Set constant API timeout
API_TIMEOUT = 10


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
            
            # API returns array wuth single quote
            if data and len(data) > 0:
                quote_data = data[0]

                 # Extract values using .get() to handle missing keys gracefully
                quote = quote_data.get('q')
                author = quote_data.get('a')

                # Check for missing keys or empty values (malformed data)
                if not quote or not author:
                    logger.error(
                        f"Malformed quote data received. "
                        f"'q' or 'a' key missing or value is empty. "
                        f"Keys received: {list(quote_data.keys())}"
                    )
                    return None
                
                # Data formatting (only if validation passes)
                formatted_quote = {
                    'quote': quote,
                    'author': author,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'fetched_at': datetime.now().isoformat()
                }

                logger.info(f"Today's quote: '{formatted_quote['quote'][:50]}...' by {formatted_quote['author']}")
                return formatted_quote  
            else:
                logger.error("Empty response array from API") 
                
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


# Define function to save filtered data into a json file
def save_to_json(data, filename=OUTPUT_PATH):
    """
    Saves filtered data to a JSON file.
    
    Args:
        data (list[dict]): List of quote dictionaries with 'author' and 'quote' keys.
        filename (str, optional): Output file path. Defaults to 'quote_data.json'.
    
    Note:
        Overwrites existing files. Logs success/failure.
    """
    logger.info(f"Attempting to save quote to {filename}")
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            logger.info(f"Quote successfully saved to {filename}")
            print(f"Today's quote saved: '{data['quote'][:50]}...'")
    except PermissionError:
        logger.error(f"Permission denied: Cannot write to {filename}")
    except OSError as e:
        logger.error(f"OS error while saving file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while trying to save to file: {e}", exc_info=True)


def load_cached_quote(filename=OUTPUT_PATH):
    """
    Load cached quote from file if it exists and is from today
    
    Returns:
        dict or None: Quote data if valid cache exists
    """
    try:
        if not os.path.exists(filename):
            return None
            
        with open(filename, 'r') as file:
            cached_data = json.load(file)
        
        # Check if cache is from today
        today = datetime.now().strftime('%Y-%m-%d')
        if cached_data.get('date') == today:
            logger.info(f"Quote for today ({today}) already cached")
            return cached_data
        else:
            logger.info(f"Cached quote is old (from {cached_data.get('date')}), fetching new one")
            return None
            
    except Exception as e:
        logger.warning(f"Could not load cached quote: {e}")
        return None



if __name__ == "__main__":
    """
    Fetch today's quote from ZenQuotes API and cache
    - Checks if cached quote is recent otherwise run fetch  
    """
    try:
        logger.info("=" * 50)
        logger.info("Starting daily quote fetch")
        logger.info("=" * 50)

        # Check if there's today's quote cached
        cached_quote = load_cached_quote()

        if cached_quote:
            print(f"Already have today's quote cached")
        else:
            api_data = fetch_api_data(zq_today_api) 

            if api_data:  # Only proceed if data was successfully fetched
                save_to_json(api_data) 
                logger.info("sucessfully fetched and saved today's quote")
                print(f"Successfully saved quote to {OUTPUT_PATH}")
                logger.info("Script executed successfully")
        
            else:
                logger.error("Failed to fetch data from API")
                raise

    except Exception as e:
        print(f"Critical error. Check logs: {LOG_PATH}")
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)
        raise
       