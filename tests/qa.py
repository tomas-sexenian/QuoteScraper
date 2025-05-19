import json
import pandas as pd
from jsonschema import validate, ValidationError
from pathlib import Path

from src.scraper.utils.constants import DATA_FILE, QA_REPORT_FILE


def run_qa():
    data_path = Path(DATA_FILE)
    qa_report_path = Path(QA_REPORT_FILE)

    with data_path.open() as f:
        pages = json.load(f)

    page_numbers = [page.get("page") for page in pages]
    duplicate_pages = [
        page for page in set(page_numbers) if page_numbers.count(page) > 1
    ]

    all_quotes = []
    for page in pages:
        page_number = page.get("page")
        page_url = page.get("url")
        for quote in page.get("quotes", []):
            all_quotes.append({
                "page": page_number,
                "page_url": page_url,
                "text": quote.get("text"),
                "author": quote.get("author"),
                "author_url": quote.get("author_url"),
                "tags": quote.get("tags"),
                "goodreads_url": quote.get("goodreads_url")
            })

    df = pd.DataFrame(all_quotes)

    schema_path = Path(__file__).parent / "schema.json"
    with schema_path.open() as schema_file:
        schema = json.load(schema_file)

    def is_present(value):
        if value is None:
            return False
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False
        return True

    field_coverage = (df.map(is_present).mean() * 100).round(2).to_dict()

    valid_count = 0
    invalid_count = 0
    for i, row in df.iterrows():
        try:
            validate(instance=row.to_dict(), schema=schema)
            valid_count += 1
        except ValidationError:
            invalid_count += 1

    def is_valid_url(url):
        return isinstance(url, str) and url.startswith("http")

    invalid_urls = {
        "page_url": df[~df["page_url"].apply(is_valid_url)]["page_url"].tolist(),
        "author_url": df[~df["author_url"].apply(is_valid_url)]["author_url"].tolist(),
        "goodreads_url": df[~df["goodreads_url"].apply(is_valid_url)]["goodreads_url"].tolist()
    }

    with qa_report_path.open("w") as f:
        f.write("QA REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write("Field Coverage (% of non-null values):\n")
        for field, pct in field_coverage.items():
            f.write(f"- {field}: {pct}%\n")

        f.write("\nSchema Validation:\n")
        f.write(f"- Valid records: {valid_count}\n")
        f.write(f"- Invalid records: {invalid_count}\n")

        f.write("\nItem Coverage:\n")
        f.write(
            "- In a real-world production environment, item coverage tests would typically "
            "be performed by either comparing the results against the average of previous runs "
            "or by validating them against a known source such as a sitemap.\n"
        )

        f.write("\nUniqueness Check (Page Field):\n")
        if duplicate_pages:
            f.write(f"- Duplicate pages found: {sorted(duplicate_pages)}\n")
        else:
            f.write("- All pages are unique.\n")

        f.write("\nURL Validation:\n")
        for field, urls in invalid_urls.items():
            if urls:
                f.write(f"- Invalid {field}: {len(urls)} occurrences\n")
            else:
                f.write(f"- All {field} values are valid URLs\n")

        additional_qa = """
        
=================================================================================================================================

Additional QA tests that could be included:

1. **Author Validation**:
- Verify that the same author name links to a consistent author_url.
- Detect common misspellings or inconsistent casing in author names.

2. **Quote Text Validation**:
- Check for duplicate quotes across pages.
- Validate quote length (e.g., minimum/maximum character count).

3. **Tag Analysis**:
- Identify quotes with missing or empty tags.
- Analyze tag distribution to detect anomalies (e.g., overused tags).

4. **Pagination Consistency**:
- Ensure that page numbers are sequential and complete (e.g., no skipped pages).

5. **Temporal Comparison**:
- Compare current data against previous snapshots to detect:
    - Removed or missing quotes.
    - Large sudden changes in total number of quotes (potential scraping failure).

6. **Performance Metrics**:
- Record time taken per QA stage to help with profiling or debugging large datasets.

7. **Rate Limit Detection Aid**:
- Count and log any obviously repeated pages or patterns that suggest partial blocking or rate limiting effects.

=================================================================================================================================
"""

        f.write(additional_qa)
