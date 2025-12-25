import os
import pandas as pd
import logging
from datetime import datetime
from scraper.fetch_data import get_html
from scraper.parse_data import extract_data

# Configuration
URL = "https://quotes.toscrape.com/"
OUTPUT_DIR = "reports"
LOG_DIR = "logs"

# Ensure output and log directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    """Configure logging to both file and console."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create file handler
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log'))
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def save_data(data):
    """Save data to CSV and Excel files."""
    try:
        df = pd.DataFrame(data)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to CSV
        csv_file = os.path.join(OUTPUT_DIR, f'scraped_data_{timestamp}.csv')
        df.to_csv(csv_file, index=False)
        logging.info(f"Data saved to {csv_file}")
        
        # Save to Excel
        excel_file = os.path.join(OUTPUT_DIR, f'scraped_data_{timestamp}.xlsx')
        df.to_excel(excel_file, index=False, engine='openpyxl')
        logging.info(f"Data saved to {excel_file}")
        
        return True
    except Exception as e:
        logging.error(f"Error saving data: {str(e)}")
        return False

def run_scraper():
    """Main function to run the web scraper."""
    try:
        logging.info("Starting web scraper...")
        
        # Fetch HTML content
        logging.info(f"Fetching data from {URL}")
        html = get_html(URL)
        
        # Extract data
        logging.info("Extracting data from HTML")
        data = extract_data(html)
        
        if not data:
            logging.warning("No data was extracted from the page")
            return False
            
        # Save data
        logging.info(f"Saving {len(data)} records")
        if save_data(data):
            logging.info("Scraping completed successfully")
            return True
        else:
            logging.error("Failed to save data")
            return False
            
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    setup_logging()
    run_scraper()
