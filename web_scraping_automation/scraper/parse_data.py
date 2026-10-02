from bs4 import BeautifulSoup
from datetime import datetime

def extract_data(html):
    """
    Extracts quotes and authors from the HTML content.
    
    Args:
        html (str): HTML content of the page
        
    Returns:
        list: List of dictionaries containing quote information
    """
    soup = BeautifulSoup(html, "html.parser")
    quotes = soup.find_all("div", class_="quote")

    data = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for quote in quotes:
        try:
            text = quote.find("span", class_="text").text
            author = quote.find("small", class_="author").text
            
            data.append({
                "Quote": text,
                "Author": author,
                "Scraped_At": current_time
            })
        except AttributeError as e:
            print(f"Error parsing quote: {e}")
            continue

    return data
