import requests

def get_html(url):
    """
    Fetches HTML content from the specified URL.
    
    Args:
        url (str): The URL to fetch HTML from
        
    Returns:
        str: The HTML content of the page
        
    Raises:
        requests.RequestException: If the request fails
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        raise
