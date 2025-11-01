# Import required packages
import logging
import requests

# Setup logging config
logging.basicConfig(
    filename='logs/api_ingest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Assign Zenquotes (quote only) api url to a variable zp_api
zq_api = "https://zenquotes.io/api/quotes/"

# Create function to connect to api and fetch data
def fetch_api_data(url):
    """ This function takes the api url as argument.
    Connects to the api, fetches the data and parses it to JSON format.
    Returns a json format data.
    """
    try:
        logger.info(f"Attempting to fetch data from {url}")
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info("Data successfully retrieved and parsed into JSON")
            return data
        else:
            logger.error(f"Failed to retrieve data.\nStatus code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
    
    except ValueError as e:
        logger.error(f"Failed to parse data into JSON: {str(e)}")
        return None
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info =True)
        return None

