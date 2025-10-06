#!/usr/bin/env python3
"""
Bible Dictionary Scraper for LDS Scripture Study Helps

Scrapes all entries from the LDS Bible Dictionary and saves them as markdown files.
Each entry includes the entry title and full encyclopedic text content.
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bible_dictionary_scraping.log'),
        logging.StreamHandler()
    ]
)

class BibleDictionaryScraper:
    """Scraper for LDS Bible Dictionary"""

    BASE_URL = "https://www.churchofjesuschrist.org"
    INDEX_URL = f"{BASE_URL}/study/scriptures/bd?lang=eng"

    def __init__(self, output_dir="study_helps/bible_dictionary"):
        """Initialize scraper with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url, retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                logging.info(f"Fetching: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    logging.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
        return None

    def discover_entries(self):
        """Discover all entries from the index page"""
        logging.info("Discovering entries from index page...")
        html = self.fetch_page(self.INDEX_URL)
        if not html:
            logging.error("Failed to fetch index page")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        entries = []

        # Find all links to entry pages
        # Pattern: /study/scriptures/bd/[entry-slug]?lang=eng
        links = soup.find_all('a', href=re.compile(r'/study/scriptures/bd/[^/?]+\?lang=eng'))

        for link in links:
            href = link.get('href')
            # Skip introduction page
            if 'introduction' in href:
                continue

            # Extract entry name from the link text
            entry_title = link.get_text(strip=True)
            if entry_title:
                full_url = self.BASE_URL + href if href.startswith('/') else href
                entries.append((entry_title, full_url))

        # Remove duplicates while preserving order
        seen = set()
        unique_entries = []
        for entry, url in entries:
            if url not in seen:
                seen.add(url)
                unique_entries.append((entry, url))

        logging.info(f"Discovered {len(unique_entries)} unique entries")
        return unique_entries

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def extract_entry_content(self, url):
        """Extract content from an entry page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract entry title
        title_elem = soup.find('h1')
        if not title_elem:
            # Try alternative selectors
            title_elem = soup.find('title')

        entry_title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown Entry"

        # Extract main body content
        body = soup.find('div', class_='body')
        if not body:
            logging.warning(f"No body content found for {url}")
            return None

        # Extract all paragraphs
        paragraphs = body.find_all('p')

        # Combine paragraphs with double newlines between them
        body_text = '\n\n'.join([self.clean_text(p.get_text()) for p in paragraphs if p.get_text(strip=True)])

        if not body_text:
            logging.warning(f"No text content found for {url}")
            return None

        return {
            'title': entry_title,
            'url': url,
            'body': body_text
        }

    def save_entry(self, entry_data):
        """Save entry data as markdown file"""
        if not entry_data:
            return

        # Create filename from entry title
        filename = f"{entry_data['title']}.md"
        # Clean filename of invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filepath = self.output_dir / filename

        # Build markdown content
        content = f"Entry: {entry_data['title']}\n"
        content += f"URL: {entry_data['url']}\n\n"
        content += "---\n\n"
        content += entry_data['body']
        content += "\n"

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename}")
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")

    def scrape_all(self):
        """Scrape all entries"""
        logging.info("Starting Bible Dictionary scraping...")

        # Discover all entries
        entries = self.discover_entries()
        if not entries:
            logging.error("No entries discovered")
            return

        logging.info(f"Found {len(entries)} entries to scrape")

        # Scrape each entry
        successful = 0
        failed = 0

        for i, (entry_title, url) in enumerate(entries, 1):
            logging.info(f"[{i}/{len(entries)}] Processing: {entry_title}")

            try:
                entry_data = self.extract_entry_content(url)
                if entry_data:
                    self.save_entry(entry_data)
                    successful += 1
                else:
                    logging.warning(f"Failed to extract content for: {entry_title}")
                    failed += 1
            except Exception as e:
                logging.error(f"Error processing {entry_title}: {e}")
                failed += 1

            # Rate limiting
            time.sleep(2)

        logging.info(f"\nScraping complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"Total: {len(entries)}")

def main():
    scraper = BibleDictionaryScraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()
