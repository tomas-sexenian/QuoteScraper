from pathlib import Path

from src.scraper.utils.constants import DATA_FILE, LOG_FILE, QA_REPORT_FILE, BASE_SITE_URL, QUOTES_USERNAME, \
    QUOTES_PASSWORD
from src.scraper.scraper_runner import run_scraper
from src.scraper.utils.setup_utils import setup_logger, clear_last_execution_data
from tests.qa import run_qa

BASE_DIR = Path(__file__).resolve().parent


def main():
    """
    Entry point to run the quote scraper with predefined credentials and URL.
    """
    clear_last_execution_data()
    setup_logger(str(BASE_DIR / LOG_FILE))

    site_url: str = BASE_SITE_URL
    username: str = QUOTES_USERNAME
    password: str = QUOTES_PASSWORD
    output_json_path: str = DATA_FILE

    try:
        print(f"Scraping to {BASE_SITE_URL} started")
        run_scraper(site_url, username, password, output_json_path)
        print(f"Scraping completed. Data saved to '{output_json_path}'.")
        run_qa()
        print(f"QA report generated at {QA_REPORT_FILE}")
    except Exception as e:
        print(f"An error occurred while scraping: {e}")


if __name__ == "__main__":
    main()
