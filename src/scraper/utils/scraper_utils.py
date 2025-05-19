import random
from typing import Optional

from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import json
import os

from src.scraper.utils.setup_utils import get_logger

logger = get_logger(__name__)


def exponential_backoff(
        retry_count: int,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
) -> float:
    """
    Calculate delay for exponential backoff with jitter.

    Args:
        retry_count: Current retry attempt count (starting from 0)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Calculated delay in seconds
    """
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    return delay + jitter


def handle_request_exception(
        exception: RequestException,
        retry_count: int,
        max_retries: int = 3,
) -> Optional[float]:
    """
    Handle request exceptions and determine if retry is needed.

    Args:
        exception: The exception that occurred
        retry_count: Current retry count
        max_retries: Maximum number of retries

    Returns:
        Delay in seconds if retry is needed, None otherwise
    """
    if retry_count >= max_retries:
        logger.warning("Max retries reached. Will not retry.")
        return None

    if isinstance(exception, RequestException):
        delay = exponential_backoff(retry_count)
        logger.info("Retrying after %.2f seconds due to exception: %s", delay, type(exception).__name__)
        return delay

    return None


def safe_select(
        element: BeautifulSoup,
        selector: str,
        attr: Optional[str] = None,
        required: bool = True,
        default: str = ""
) -> str:
    """
    Safely select text or an attribute from the first element matching the CSS selector.
    If attr is None, returns the element's text; otherwise returns the specified attribute.
    Logs a warning and raises ValueError if required and not found; otherwise returns default.
    """
    el = element.select_one(selector)
    if el is None:
        if required:
            logger.warning("Missing selector: %s", selector)
            raise ValueError(f"Missing selector: {selector}")
        return default
    if attr:
        if el.has_attr(attr):
            return el[attr]
        if required:
            logger.warning("Missing attribute '%s' for selector: %s", attr, selector)
            raise ValueError(f"Missing attribute '{attr}' for selector: {selector}")
        return default
    return el.get_text(strip=True)


def append_page_data(
        page_url: str,
        page_quotes: list,
        output_file: str):
    """
    Appends quotes from a page to a JSON file in a structured format.

    Each entry includes the page number, URL, and a list of quotes.
    If the file exists, existing data is loaded and updated; otherwise, a new list is created.
    If the page number is not found in the URL, it defaults to 1.

    Args:
        page_url (str): URL of the scraped page.
        page_quotes (list): List of quote dictionaries from the page.
        output_file (str): Path to the output JSON file.
    """
    logger.debug("Appending data for page URL: %s", page_url)

    data = []
    if os.path.exists(output_file):
        logger.debug("Output file exists. Attempting to load existing data from: %s", output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                logger.debug("Loaded existing data with %d entries.", len(data))
            except json.JSONDecodeError as e:
                logger.warning("Failed to decode existing JSON file. Starting with empty data. Error: %s", e)
                data = []

    last_part = page_url.rstrip("/").split("/")[-1]
    try:
        page_number = int(last_part)
    except ValueError:
        logger.debug("No valid page number in URL; defaulting to 1.")
        page_number = 1

    page_data = {
        "page": page_number,
        "url": page_url,
        "quotes": [quote.model_dump(mode="json") for quote in page_quotes]
    }

    data.append(page_data)
    logger.info("Appending data for page %d with %d quotes.", page_number, len(page_quotes))

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            logger.debug("Successfully wrote updated data to file: %s", output_file)
    except Exception as e:
        logger.exception("Failed to write data to file: %s", e)
