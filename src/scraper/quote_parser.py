from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.scraper.utils.auth import QuoteScraperAuth
from src.scraper.utils.constants import SESSION_GET_TIMEOUT
from src.data.models import Quote, Tag
from src.scraper.utils.scraper_utils import safe_select
from src.scraper.utils.setup_utils import get_logger

logger = get_logger(__name__)


class QuotePageParser:
    """
    Parses quotes from the site with fail-safe selectors.
    """

    def __init__(self, auth: QuoteScraperAuth):
        self.auth = auth
        self.session = auth.session

    def extract_quote_fields(self, quote_element: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract raw quote fields into a dictionary.
        """
        text = safe_select(quote_element, 'span.text')
        text = text.strip('“”')

        author = safe_select(quote_element, 'small.author')

        author_rel = safe_select(
            quote_element,
            'a[href^="/author/"]',
            attr='href'
        )
        author_url = urljoin(self.auth.base_url, author_rel)

        tags: List[Dict[str, str]] = []
        for tag_el in quote_element.select('div.tags a.tag'):
            name = tag_el.get_text(strip=True)
            href = tag_el.get('href', '')
            if not name or not href:
                logger.warning("Skipping tag with missing name or href")
                continue
            tags.append({
                "name": name,
                "url": urljoin(self.auth.base_url, href)
            })

        goodreads_url = ""
        try:
            resp = self.session.get(author_url, timeout=SESSION_GET_TIMEOUT)
            resp.raise_for_status()
            author_soup = BeautifulSoup(resp.content, 'html.parser')
            link = author_soup.select_one('a[href*="goodreads.com"]')
            if link and link.has_attr('href'):
                goodreads_url = link['href']
            else:
                logger.warning("GoodReads link missing on author page")
        except Exception as e:
            logger.warning("Failed loading author page %s: %s", author_url, e)

        return {
            "text": text,
            "author": author,
            "author_url": author_url,
            "tags": tags,
            "goodreads_url": goodreads_url
        }

    def parse_quotes_from_page(self, page_url: str) -> List[Quote]:
        """
        Parse quotes from a page URL into a list of Quote models.
        """
        resp = self.session.get(page_url, timeout=SESSION_GET_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        quotes: List[Quote] = []
        for elem in soup.select('div.quote'):
            try:
                fields = self.extract_quote_fields(elem)
                tag_models = [Tag(**tag) for tag in fields["tags"]]
                quote = Quote(
                    text=fields["text"],
                    author=fields["author"],
                    author_url=fields["author_url"],
                    tags=tag_models,
                    goodreads_url=fields["goodreads_url"]
                )
                quotes.append(quote)
            except Exception as e:
                logger.warning("Skipping quote due to extraction error: %s", e)
        logger.info("Parsed %d quotes from page %s", len(quotes), page_url)
        return quotes

    def get_next_page_url(self, current_page_url: str, seen_urls: set) -> str:
        """
        Returns the absolute URL for the next page, or empty if none or already visited.
        """
        resp = self.session.get(current_page_url, timeout=SESSION_GET_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        href = safe_select(soup, 'li.next > a', attr='href', required=False)
        if not href:
            return ""
        next_url = urljoin(current_page_url, href)
        if next_url in seen_urls:
            logger.warning("Detected loop: already visited %s", next_url)
            return ""
        return next_url
