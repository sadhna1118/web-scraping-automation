# Web Scraping Automation

This project automates the process of scraping quotes from [Quotes to Scrape](https://quotes.toscrape.com/) and saving them to both CSV and Excel formats.

## Features

- Fetches HTML content from the target website
- Extracts quotes and authors
- Saves data in both CSV and Excel formats
- Includes comprehensive logging
- Timestamped output files
- Error handling and logging

## Prerequisites

- Python 3.7+
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd web_scraping_automation
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Scraper

To run the scraper manually:

```bash
python main.py
```

### Output

The script will create the following files:
- `reports/scraped_data_<timestamp>.csv` - CSV file containing the scraped data
- `reports/scraped_data_<timestamp>.xlsx` - Excel file containing the scraped data
- `logs/scraper.log` - Log file with detailed execution information

### Automation

#### Windows Task Scheduler
1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger (daily, weekly, etc.)
4. Action: Start a program
   - Program/script: `C:\path\to\python.exe`
   - Add arguments: `main.py`
   - Start in: `C:\path\to\web_scraping_automation`

#### Linux/Mac (Cron)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 3 AM
0 3 * * * cd /path/to/web_scraping_automation && /usr/bin/python3 main.py >> /path/to/web_scraping_automation/logs/cron.log 2>&1
```

## Project Structure

```
web_scraping_automation/
├── scraper/
│   ├── __init__.py
│   ├── fetch_data.py        # Fetches HTML content
│   └── parse_data.py        # Parses HTML and extracts data
├── reports/                 # Output directory for CSV/Excel files
├── logs/                    # Log files
├── main.py                  # Main script
└── requirements.txt         # Python dependencies
```

## License

This project is open source and available under the [MIT License](LICENSE).
