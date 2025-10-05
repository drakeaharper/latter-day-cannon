#!/usr/bin/env python3
"""
Focused scraper for New Testament
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nt_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NTScraper:
    def __init__(self):
        self.base_url = "https://www.churchofjesuschrist.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.output_dir = Path("scriptures/new-testament")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # New Testament books with chapter counts
        self.nt_books = {
            'matt': {'name': 'Matthew', 'chapters': 28},
            'mark': {'name': 'Mark', 'chapters': 16},
            'luke': {'name': 'Luke', 'chapters': 24},
            'john': {'name': 'John', 'chapters': 21},
            'acts': {'name': 'Acts', 'chapters': 28},
            'rom': {'name': 'Romans', 'chapters': 16},
            '1-cor': {'name': '1 Corinthians', 'chapters': 16},
            '2-cor': {'name': '2 Corinthians', 'chapters': 13},
            'gal': {'name': 'Galatians', 'chapters': 6},
            'eph': {'name': 'Ephesians', 'chapters': 6},
            'philip': {'name': 'Philippians', 'chapters': 4},
            'col': {'name': 'Colossians', 'chapters': 4},
            '1-thes': {'name': '1 Thessalonians', 'chapters': 5},
            '2-thes': {'name': '2 Thessalonians', 'chapters': 3},
            '1-tim': {'name': '1 Timothy', 'chapters': 6},
            '2-tim': {'name': '2 Timothy', 'chapters': 4},
            'titus': {'name': 'Titus', 'chapters': 3},
            'philem': {'name': 'Philemon', 'chapters': 1},
            'heb': {'name': 'Hebrews', 'chapters': 13},
            'james': {'name': 'James', 'chapters': 5},
            '1-pet': {'name': '1 Peter', 'chapters': 5},
            '2-pet': {'name': '2 Peter', 'chapters': 3},
            '1-jn': {'name': '1 John', 'chapters': 5},
            '2-jn': {'name': '2 John', 'chapters': 1},
            '3-jn': {'name': '3 John', 'chapters': 1},
            'jude': {'name': 'Jude', 'chapters': 1},
            'rev': {'name': 'Revelation', 'chapters': 22}
        }

    def fetch_page(self, url, max_retries=3):
        """Fetch a page with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching: {url}")
                response = self.session.get(url)
                response.raise_for_status()
                time.sleep(2)  # Rate limiting
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

    def clean_verse_text(self, verse_element):
        """Extract and clean verse text, removing study notes and markup."""
        verse_copy = verse_element.__copy__()

        # Extract verse number first
        verse_num_span = verse_copy.find('span', class_='verse-number')
        if verse_num_span:
            verse_num = verse_num_span.get_text().strip()
            verse_num_span.decompose()
        else:
            verse_num = ""

        # Remove study note references but preserve the text they contain
        for note_ref in verse_copy.find_all('a', class_='study-note-ref'):
            note_ref.replace_with(note_ref.get_text())

        # Remove any remaining sup elements (superscript references)
        for sup in verse_copy.find_all('sup'):
            sup.decompose()

        # Get the remaining text
        verse_text = verse_copy.get_text().strip()
        verse_text = re.sub(r'\s+', ' ', verse_text)

        return verse_num, verse_text

    def extract_content(self, html, url):
        """Extract content from HTML."""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        title_element = soup.find('h1')
        title = title_element.get_text().strip() if title_element else ""

        # Extract chapter summary if available
        summary_element = soup.find('p', class_='study-summary')
        summary = summary_element.get_text().strip() if summary_element else ""

        # Extract verses
        verses = []
        verse_elements = soup.find_all('p', class_='verse')

        for verse_element in verse_elements:
            verse_num, verse_text = self.clean_verse_text(verse_element)
            if verse_text:  # Only add non-empty verses
                verses.append((verse_num, verse_text))

        return {
            'title': title,
            'summary': summary,
            'verses': verses,
            'url': url
        }

    def format_file(self, book_name, chapter_num, content):
        """Format content for file output."""
        lines = [
            f"Collection: New Testament",
            f"Book: {book_name}",
            f"Chapter: {chapter_num}",
            f"Title: {content['title']}",
            f"URL: {content['url']}",
            "",
            "---",
            ""
        ]

        # Add summary if available
        if content['summary']:
            lines.extend([content['summary'], ""])

        # Add verses
        for verse_num, verse_text in content['verses']:
            if verse_num:
                lines.append(f"{verse_num} {verse_text}")
            else:
                lines.append(verse_text)
            lines.append("")  # Empty line between verses

        return "\n".join(lines)

    def save_chapter(self, book_name, chapter_num, content):
        """Save chapter content to file."""
        filename = f"[New Testament][{book_name}][Chapter {chapter_num}].md"
        filepath = self.output_dir / filename
        formatted_content = self.format_file(book_name, chapter_num, content)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False

    def scrape_chapter(self, book_abbr, book_name, chapter_num):
        """Scrape a single chapter."""
        url = f"{self.base_url}/study/scriptures/nt/{book_abbr}/{chapter_num}?lang=eng"

        html = self.fetch_page(url)
        if not html:
            return False

        content = self.extract_content(html, url)
        if not content['verses']:
            logger.warning(f"No verses found for {book_name} Chapter {chapter_num}")
            return False

        return self.save_chapter(book_name, chapter_num, content)

    def scrape_all(self):
        """Scrape all New Testament books."""
        logger.info("Starting New Testament scraping...")

        total_chapters = sum(book['chapters'] for book in self.nt_books.values())
        completed = 0
        failed = 0
        processed = 0

        for book_abbr, book_info in self.nt_books.items():
            book_name = book_info['name']
            chapters = book_info['chapters']

            logger.info(f"Scraping {book_name} ({chapters} chapters)...")

            for chapter in range(1, chapters + 1):
                if self.scrape_chapter(book_abbr, book_name, chapter):
                    completed += 1
                else:
                    failed += 1

                processed += 1
                logger.info(f"Progress: {processed}/{total_chapters} chapters processed ({processed/total_chapters*100:.1f}%)")

        logger.info(f"New Testament scraping complete! {completed} successful, {failed} failed")
        return completed, failed

def main():
    scraper = NTScraper()
    completed, failed = scraper.scrape_all()

    print(f"\nNew Testament Scraping Summary:")
    print(f"Successfully scraped: {completed} chapters")
    print(f"Failed: {failed} chapters")
    print(f"Output directory: {scraper.output_dir}")

if __name__ == "__main__":
    main()