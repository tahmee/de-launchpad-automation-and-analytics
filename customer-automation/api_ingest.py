# Import required packages
import logging
import requests
import json

# Setup logging config
logging.basicConfig(
    filename='logs/api_ingest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Assign Zenquotes(quote only) API url to a variable zq_api
zq_api = "https://zenquotes.io/api/quotes/"

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
        response = requests.get(url, timeout=10)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info("Data successfully retrieved and parsed into JSON")
            return data
        else:
            logger.error(f"Failed to retrieve data.\nStatus code: {response.status_code}")
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
    logger.info(f"Starting data filtering.\n{len(data)} records to process")
    selected_data = []
    skipped_record = 0
    
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
            skipped_record += 1
            continue  # Skip malformed items, process the rest
        except Exception as e:
            logger.error(f"Unexpected error processing item: {e}")
    logger.info(f"Successfully filtered {len(selected_data)} records.\nSkipped {skipped_record} records")
    return selected_data

# Define function to save filtered data into a .json file
def save_to_json(data, filename='quote_data.json'):
    """
     Saves filtered data to a JSON file.
    
    Args:
        data (list[dict]): List of quote dictionaries with 'author' and 'quote' keys.
        filename (str, optional): Output file path. Defaults to 'quote_data.json'.
    
    Note:
        Overwrites existing files. Logs success/failure.
    """
    logger.info(f"Attempting to save {data} in {filename}")
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            logging.info(f"Filtered data successfully saved to {filename}")
    except PermissionError:
        logger.error(f"Permission denied: Cannot write to {filename}")
    except Exception as e:
        logger.error(f"Unexpected error while trying to save to JSON file: {e}", exc_info=True)


if __name__ == "__main__":
    #Fetch quotes from Zenquotes API, filter to author/quote pairs, and save locally.
    try:
        logger.info("BEGIN------------------------------")
        api_data = fetch_api_data(zq_api) 
        if api_data:  # Only proceed if data was successfully fetched
            new_data = filter_data(api_data) 
            save_to_json(new_data) 
            logger.info("Script executed successfully")
    except Exception as e:
        logger.critical(f"Script failed; Unexpected error: {e}", exc_info=True)