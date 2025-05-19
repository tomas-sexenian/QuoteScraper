from requests import Session
from bs4 import BeautifulSoup

from src.scraper.utils.constants import SESSION_GET_TIMEOUT, BASE_SITE_URL
from src.scraper.utils.scraper_utils import safe_select
from src.scraper.utils.setup_utils import get_logger

logger = get_logger(__name__)


class QuoteScraperAuth:
    """Handles authentication for the quotes.toscrape.com website."""

    def __init__(self, base_url: str = BASE_SITE_URL):
        self.base_url = base_url
        self.session = Session()

    def login(self, username: str, password: str) -> bool:
        """
        Authenticate with the quotes' website.

        Args:
            username: The username to log in with
            password: The password to log in with

        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            login_url = f"{self.base_url}/login"
            resp = self.session.get(login_url, timeout=SESSION_GET_TIMEOUT)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_token = safe_select(
                soup,
                'input[name="csrf_token"]',
                attr='value'
            )
        except Exception as e:
            logger.error("Failed to retrieve CSRF token: %s", e)
            return False

        payload = {
            'csrf_token': csrf_token,
            'username': username,
            'password': password
        }

        try:
            post_resp = self.session.post(login_url, data=payload, timeout=SESSION_GET_TIMEOUT)
            post_resp.raise_for_status()
        except Exception as e:
            logger.warning("Login POST request failed: %s", e)
            return False

        success = "Logout" in post_resp.text
        if success:
            logger.info("Login successful for user: %s", username)
        else:
            logger.warning("Login failed. 'Logout' not found in response.")
        return success

    def is_authenticated(self) -> bool:
        """
        Check if the current session is authenticated.

        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            home_resp = self.session.get(self.base_url, timeout=SESSION_GET_TIMEOUT)
            home_resp.raise_for_status()
            authenticated = "Logout" in home_resp.text
            logger.info("Session is %sauthenticated.", "" if authenticated else "not ")
            return authenticated
        except Exception as e:
            logger.warning("Failed to verify authentication: %s", e)
            return False
