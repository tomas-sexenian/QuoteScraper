from pathlib import Path

BASE_SITE_URL = "https://quotes.toscrape.com/"
QUOTES_USERNAME = "admin"
QUOTES_PASSWORD = "password"

SESSION_GET_TIMEOUT = 10

OUTPUT_FOLDER = Path("outputs")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
DATA_FILE = OUTPUT_FOLDER / "data.json"
LOG_FILE = OUTPUT_FOLDER / "client.log"
QA_REPORT_FILE = OUTPUT_FOLDER / "qa_report.txt"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
