#!/usr/bin/env python3
"""
Parallel Scripture Scraper
Launches all remaining collections in parallel and monitors progress
"""

import subprocess
import time
import json
from pathlib import Path
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParallelScraper:
    def __init__(self):
        self.collections = {
            'nt': {
                'name': 'New Testament',
                'script': 'scrape_nt.py',
                'estimated_files': 260,
                'process': None,
                'completed': 0,
                'failed': 0,
                'status': 'pending'
            },
            'bofm': {
                'name': 'Book of Mormon',
                'script': 'scrape_bofm.py',
                'estimated_files': 239,
                'process': None,
                'completed': 0,
                'failed': 0,
                'status': 'pending'
            },
            'ot': {
                'name': 'Old Testament',
                'script': 'scrape_ot.py',
                'estimated_files': 929,
                'process': None,
                'completed': 0,
                'failed': 0,
                'status': 'pending'
            }
        }

        # Check if NT is already running
        self.nt_already_started = True  # Since we started it already

    def create_bofm_scraper(self):
        """Create Book of Mormon scraper"""
        script_content = '''#!/usr/bin/env python3
"""
Focused scraper for Book of Mormon
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
        logging.FileHandler('bofm_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BoFMScraper:
    def __init__(self):
        self.base_url = "https://www.churchofjesuschrist.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.output_dir = Path("scriptures/book-of-mormon")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Book of Mormon books with chapter counts
        self.bofm_books = {
            '1-ne': {'name': '1 Nephi', 'chapters': 22},
            '2-ne': {'name': '2 Nephi', 'chapters': 33},
            'jacob': {'name': 'Jacob', 'chapters': 7},
            'enos': {'name': 'Enos', 'chapters': 1},
            'jarom': {'name': 'Jarom', 'chapters': 1},
            'omni': {'name': 'Omni', 'chapters': 1},
            'w-of-m': {'name': 'Words of Mormon', 'chapters': 1},
            'mosiah': {'name': 'Mosiah', 'chapters': 29},
            'alma': {'name': 'Alma', 'chapters': 63},
            'hel': {'name': 'Helaman', 'chapters': 16},
            '3-ne': {'name': '3 Nephi', 'chapters': 30},
            '4-ne': {'name': '4 Nephi', 'chapters': 1},
            'morm': {'name': 'Mormon', 'chapters': 9},
            'ether': {'name': 'Ether', 'chapters': 15},
            'moro': {'name': 'Moroni', 'chapters': 10}
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
        verse_text = re.sub(r'\\s+', ' ', verse_text)

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
            f"Collection: Book of Mormon",
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

        return "\\n".join(lines)

    def save_chapter(self, book_name, chapter_num, content):
        """Save chapter content to file."""
        filename = f"[Book of Mormon][{book_name}][Chapter {chapter_num}].md"
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
        url = f"{self.base_url}/study/scriptures/bofm/{book_abbr}/{chapter_num}?lang=eng"

        html = self.fetch_page(url)
        if not html:
            return False

        content = self.extract_content(html, url)
        if not content['verses']:
            logger.warning(f"No verses found for {book_name} Chapter {chapter_num}")
            return False

        return self.save_chapter(book_name, chapter_num, content)

    def scrape_all(self):
        """Scrape all Book of Mormon books."""
        logger.info("Starting Book of Mormon scraping...")

        total_chapters = sum(book['chapters'] for book in self.bofm_books.values())
        completed = 0
        failed = 0
        processed = 0

        for book_abbr, book_info in self.bofm_books.items():
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

        logger.info(f"Book of Mormon scraping complete! {completed} successful, {failed} failed")
        return completed, failed

def main():
    scraper = BoFMScraper()
    completed, failed = scraper.scrape_all()

    print(f"\\nBook of Mormon Scraping Summary:")
    print(f"Successfully scraped: {completed} chapters")
    print(f"Failed: {failed} chapters")
    print(f"Output directory: {scraper.output_dir}")

if __name__ == "__main__":
    main()
'''

        with open('scrape_bofm.py', 'w') as f:
            f.write(script_content)

    def create_ot_scraper(self):
        """Create Old Testament scraper with most common books"""
        script_content = '''#!/usr/bin/env python3
"""
Focused scraper for Old Testament
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
        logging.FileHandler('ot_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OTScraper:
    def __init__(self):
        self.base_url = "https://www.churchofjesuschrist.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.output_dir = Path("scriptures/old-testament")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Old Testament books with chapter counts (major ones)
        self.ot_books = {
            'gen': {'name': 'Genesis', 'chapters': 50},
            'ex': {'name': 'Exodus', 'chapters': 40},
            'lev': {'name': 'Leviticus', 'chapters': 27},
            'num': {'name': 'Numbers', 'chapters': 36},
            'deut': {'name': 'Deuteronomy', 'chapters': 34},
            'josh': {'name': 'Joshua', 'chapters': 24},
            'judg': {'name': 'Judges', 'chapters': 21},
            'ruth': {'name': 'Ruth', 'chapters': 4},
            '1-sam': {'name': '1 Samuel', 'chapters': 31},
            '2-sam': {'name': '2 Samuel', 'chapters': 24},
            '1-kgs': {'name': '1 Kings', 'chapters': 22},
            '2-kgs': {'name': '2 Kings', 'chapters': 25},
            '1-chr': {'name': '1 Chronicles', 'chapters': 29},
            '2-chr': {'name': '2 Chronicles', 'chapters': 36},
            'ezra': {'name': 'Ezra', 'chapters': 10},
            'neh': {'name': 'Nehemiah', 'chapters': 13},
            'esth': {'name': 'Esther', 'chapters': 10},
            'job': {'name': 'Job', 'chapters': 42},
            'ps': {'name': 'Psalms', 'chapters': 150},
            'prov': {'name': 'Proverbs', 'chapters': 31},
            'eccl': {'name': 'Ecclesiastes', 'chapters': 12},
            'song': {'name': 'Song of Solomon', 'chapters': 8},
            'isa': {'name': 'Isaiah', 'chapters': 66},
            'jer': {'name': 'Jeremiah', 'chapters': 52},
            'lam': {'name': 'Lamentations', 'chapters': 5},
            'ezek': {'name': 'Ezekiel', 'chapters': 48},
            'dan': {'name': 'Daniel', 'chapters': 12},
            'hosea': {'name': 'Hosea', 'chapters': 14},
            'joel': {'name': 'Joel', 'chapters': 3},
            'amos': {'name': 'Amos', 'chapters': 9},
            'obad': {'name': 'Obadiah', 'chapters': 1},
            'jonah': {'name': 'Jonah', 'chapters': 4},
            'micah': {'name': 'Micah', 'chapters': 7},
            'nahum': {'name': 'Nahum', 'chapters': 3},
            'hab': {'name': 'Habakkuk', 'chapters': 3},
            'zeph': {'name': 'Zephaniah', 'chapters': 3},
            'hag': {'name': 'Haggai', 'chapters': 2},
            'zech': {'name': 'Zechariah', 'chapters': 14},
            'mal': {'name': 'Malachi', 'chapters': 4}
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
        verse_text = re.sub(r'\\s+', ' ', verse_text)

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
            f"Collection: Old Testament",
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

        return "\\n".join(lines)

    def save_chapter(self, book_name, chapter_num, content):
        """Save chapter content to file."""
        filename = f"[Old Testament][{book_name}][Chapter {chapter_num}].md"
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
        url = f"{self.base_url}/study/scriptures/ot/{book_abbr}/{chapter_num}?lang=eng"

        html = self.fetch_page(url)
        if not html:
            return False

        content = self.extract_content(html, url)
        if not content['verses']:
            logger.warning(f"No verses found for {book_name} Chapter {chapter_num}")
            return False

        return self.save_chapter(book_name, chapter_num, content)

    def scrape_all(self):
        """Scrape all Old Testament books."""
        logger.info("Starting Old Testament scraping...")

        total_chapters = sum(book['chapters'] for book in self.ot_books.values())
        completed = 0
        failed = 0
        processed = 0

        for book_abbr, book_info in self.ot_books.items():
            book_name = book_info['name']
            chapters = book_info['chapters']

            logger.info(f"Scraping {book_name} ({chapters} chapters)...")

            for chapter in range(1, chapters + 1):
                if self.scrape_chapter(book_abbr, book_name, chapter):
                    completed += 1
                else:
                    failed += 1

                processed += 1
                if processed % 10 == 0:  # Log every 10 chapters to reduce spam
                    logger.info(f"Progress: {processed}/{total_chapters} chapters processed ({processed/total_chapters*100:.1f}%)")

        logger.info(f"Old Testament scraping complete! {completed} successful, {failed} failed")
        return completed, failed

def main():
    scraper = OTScraper()
    completed, failed = scraper.scrape_all()

    print(f"\\nOld Testament Scraping Summary:")
    print(f"Successfully scraped: {completed} chapters")
    print(f"Failed: {failed} chapters")
    print(f"Output directory: {scraper.output_dir}")

if __name__ == "__main__":
    main()
'''

        with open('scrape_ot.py', 'w') as f:
            f.write(script_content)

    def start_collection(self, collection_key):
        """Start scraping a collection in background"""
        collection = self.collections[collection_key]

        if collection_key == 'nt' and self.nt_already_started:
            logger.info(f"{collection['name']} already started")
            collection['status'] = 'running'
            return True

        script_path = collection['script']

        if collection_key == 'bofm':
            self.create_bofm_scraper()
        elif collection_key == 'ot':
            self.create_ot_scraper()

        try:
            process = subprocess.Popen(
                ['python3', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            collection['process'] = process
            collection['status'] = 'running'
            logger.info(f"Started {collection['name']} scraping (PID: {process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start {collection['name']}: {e}")
            collection['status'] = 'failed'
            return False

    def monitor_progress(self):
        """Monitor progress of all running collections"""
        while True:
            all_done = True

            for key, collection in self.collections.items():
                if collection['status'] == 'running':
                    all_done = False

                    # Check if process is still running
                    if collection['process'] and collection['process'].poll() is not None:
                        # Process finished
                        return_code = collection['process'].returncode
                        if return_code == 0:
                            collection['status'] = 'completed'
                            logger.info(f"{collection['name']} completed successfully")
                        else:
                            collection['status'] = 'failed'
                            logger.error(f"{collection['name']} failed with return code {return_code}")

            if all_done:
                break

            # Print status summary
            self.print_status()
            time.sleep(30)  # Check every 30 seconds

    def print_status(self):
        """Print current status of all collections"""
        logger.info("\\n" + "="*60)
        logger.info("PARALLEL SCRAPING STATUS")
        logger.info("="*60)

        total_estimated = 0
        total_running = 0

        for key, collection in self.collections.items():
            status_emoji = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(collection['status'], '❓')

            logger.info(f"{status_emoji} {collection['name']}: {collection['status']} ({collection['estimated_files']} files)")
            total_estimated += collection['estimated_files']

            if collection['status'] == 'running':
                total_running += 1

        logger.info(f"\\nTotal estimated files: {total_estimated}")
        logger.info(f"Collections running: {total_running}")
        logger.info("="*60)

    def start_all(self):
        """Start all collections in parallel"""
        logger.info("Starting parallel scripture scraping...")

        # Start all collections
        for key in self.collections.keys():
            if not self.start_collection(key):
                logger.error(f"Failed to start {key}")

        # Monitor progress
        self.monitor_progress()

        # Final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print final summary"""
        logger.info("\\n" + "="*60)
        logger.info("FINAL SCRAPING SUMMARY")
        logger.info("="*60)

        for key, collection in self.collections.items():
            status_emoji = {
                'completed': '✅',
                'failed': '❌',
                'running': '🔄'
            }.get(collection['status'], '❓')

            logger.info(f"{status_emoji} {collection['name']}: {collection['status']}")

        logger.info("="*60)

def main():
    scraper = ParallelScraper()
    scraper.start_all()

if __name__ == "__main__":
    main()
'''