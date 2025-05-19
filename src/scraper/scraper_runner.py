import requests
import time
import sys
import os
from requests.exceptions import RequestException, ConnectTimeout, HTTPError
from src.scraper.utils.auth import QuoteScraperAuth
from src.scraper.quote_parser import QuotePageParser
from src.scraper.utils.scraper_utils import handle_request_exception, append_page_data
from src.scraper.utils.setup_utils import get_logger

logger = get_logger(__name__)


def login_and_get_parser(site_url: str, username: str, password: str) -> QuotePageParser:
    """
    Handles authentication and returns an authenticated QuoteParser instance.

    Raises:
        SystemExit: If authentication or initial request fails.

    Returns:
        QuotePageParser: An authenticated parser object.
    """
    logger.info("Checking initial page availability.")
    try:
        response = requests.get(site_url)
        response.raise_for_status()
        logger.info("Initial request successful.")
    except RequestException as e:
        logger.error("Initial request failed: %s", e)
        sys.exit("Exiting due to failure in initial request.")

    auth = QuoteScraperAuth()
    try:
        if not auth.login(username, password):
            logger.error("Login failed for user '%s'.", username)
            sys.exit("Exiting due to authentication failure.")
        logger.info("Authentication successful.")
    except Exception:
        logger.exception("Unexpected error during authentication for user '%s'.", username)
        sys.exit("Exiting due to authentication error.")

    return QuotePageParser(auth)


def process_single_page(parser: QuotePageParser, current_url: str, output_file: str) -> bool:
    """
    Processes a single quote page: parses quotes, appends data, logs timing.

    Returns:
        bool: True if successful, False if unrecoverable error occurs.
    """
    retry_count = 0
    max_retries = 3
    backoff_time = 1

    while True:
        try:
            start_time = time.time()
            quotes = parser.parse_quotes_from_page(current_url)
            append_page_data(current_url, quotes, output_file)
            elapsed = time.time() - start_time
            logger.info("Processed %s: %d quotes in %.2f seconds", current_url, len(quotes), elapsed)
            return True
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                logger.warning("429 Too Many Requests at %s. Backing off.", current_url)
                time.sleep(backoff_time)
                backoff_time = min(backoff_time * 2, 60)
                continue
            logger.warning("HTTP error at %s: %s", current_url, e)
            wait_time = handle_request_exception(e, retry_count, max_retries)
        except (ConnectTimeout, RequestException) as e:
            logger.warning("Request error at %s: %s", current_url, e)
            wait_time = handle_request_exception(e, retry_count, max_retries)
        except Exception:
            logger.exception("Unexpected error while processing %s", current_url)
            return False

        if wait_time:
            logger.info("Retrying in %.2f seconds (attempt %d of %d)", wait_time, retry_count + 1, max_retries)
            time.sleep(wait_time)
            retry_count += 1
        else:
            logger.error("Skipping page due to repeated failure: %s", current_url)
            return False


def scrape_all_quote_pages(parser: QuotePageParser, base_url: str, output_file: str) -> None:
    """
    Crawls all pages starting from the base URL, extracts quotes,
    and appends structured data to a JSON file.
    """
    current_url = base_url
    seen_urls = set()
    pages_scraped = 0
    delay_between_pages = 1
    max_delay = 60

    while True:
        if current_url in seen_urls:
            logger.warning("Detected loop or duplicate page: %s", current_url)
            break
        seen_urls.add(current_url)

        success = process_single_page(parser, current_url, output_file)
        if success:
            pages_scraped += 1
            delay_between_pages = max(1, delay_between_pages // 2)
        else:
            delay_between_pages = min(delay_between_pages * 2, max_delay)

        next_page_url = parser.get_next_page_url(current_url, seen_urls)
        if next_page_url:
            logger.info("Delaying %.2f seconds before next page", delay_between_pages)
            time.sleep(delay_between_pages)
            logger.info("Moving to next page: %s", next_page_url)
            current_url = next_page_url
        else:
            logger.info("Finished scraping %d pages starting from %s", pages_scraped, base_url)
            break


def run_scraper(base_url: str, username: str, password: str, output_file: str) -> None:
    """
    Entry point to run the full scraper process: login_and_get_parser and crawl.
    """
    logger.info("Running scraper for site: %s", base_url)

    quote_parser = login_and_get_parser(base_url, username, password)
    scrape_all_quote_pages(quote_parser, base_url, output_file)

    if os.path.exists(output_file):
        size_kb = os.path.getsize(output_file) / 1024
        logger.info("Scraper finished. Output saved to '%s' (%.2f KB)", output_file, size_kb)
    else:
        logger.warning("Scraper finished, but output file not found: %s", output_file)
