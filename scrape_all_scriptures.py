#!/usr/bin/env python3
"""
Comprehensive Scripture Scraper for all LDS canonical texts
Automatically discovers and scrapes all collections: Old Testament, New Testament,
Book of Mormon, Doctrine and Covenants, and Pearl of Great Price.
"""

import requests
import time
import os
import logging
from bs4 import BeautifulSoup
from pathlib import Path
import re
from urllib.parse import urljoin
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripture_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScriptureScraper:
    def __init__(self):
        self.base_url = "https://www.churchofjesuschrist.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Base directories
        self.base_dir = Path("scriptures")
        self.base_dir.mkdir(exist_ok=True)

        # Collection configurations
        self.collections = {
            'ot': {
                'name': 'Old Testament',
                'directory': 'old-testament',
                'url_path': '/study/scriptures/ot?lang=eng'
            },
            'nt': {
                'name': 'New Testament',
                'directory': 'new-testament',
                'url_path': '/study/scriptures/nt?lang=eng'
            },
            'bofm': {
                'name': 'Book of Mormon',
                'directory': 'book-of-mormon',
                'url_path': '/study/scriptures/bofm?lang=eng'
            },
            'dc-testament': {
                'name': 'Doctrine and Covenants',
                'directory': 'doctrine-and-covenants',
                'url_path': '/study/scriptures/dc-testament?lang=eng'
            }
        }

        # Create output directories
        for collection in self.collections.values():
            output_dir = self.base_dir / collection['directory']
            output_dir.mkdir(exist_ok=True)

        # Progress tracking
        self.progress = {
            'total_files': 0,
            'completed': 0,
            'failed': 0,
            'collections': {}
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

    def discover_books(self, collection_key):
        """Discover all books in a collection."""
        collection = self.collections[collection_key]
        url = self.base_url + collection['url_path']

        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        books = []

        # Look for book links in the navigation
        book_links = soup.find_all('a', href=True)

        for link in book_links:
            href = link.get('href', '')

            # Match book URLs for this collection
            pattern = f'/study/scriptures/{collection_key}/([^/]+)\\?lang=eng'
            if collection_key == 'dc-testament':
                pattern = f'/study/scriptures/{collection_key}/([^/]+)\\?lang=eng'

            match = re.search(pattern, href)
            if match:
                book_abbr = match.group(1)
                book_name = link.get_text().strip()

                # Skip if this is a chapter link (contains numbers at end)
                if not re.search(r'/\d+\?lang=eng$', href):
                    books.append({
                        'abbreviation': book_abbr,
                        'name': book_name,
                        'url': self.base_url + href
                    })

        # Remove duplicates
        seen = set()
        unique_books = []
        for book in books:
            key = book['abbreviation']
            if key not in seen:
                seen.add(key)
                unique_books.append(book)

        logger.info(f"Discovered {len(unique_books)} books in {collection['name']}")
        return unique_books

    def discover_chapters(self, collection_key, book):
        """Discover all chapters in a book."""
        html = self.fetch_page(book['url'])
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chapters = []

        # Look for chapter links in table of contents
        toc_links = soup.find_all('a', href=True)

        collection = self.collections[collection_key]

        for link in toc_links:
            href = link.get('href', '')

            # Match chapter URLs
            if collection_key == 'dc-testament':
                # For D&C, look for section numbers
                pattern = f'/study/scriptures/{collection_key}/dc/(\\d+)\\?lang=eng'
            else:
                # For other collections, look for chapter numbers
                pattern = f'/study/scriptures/{collection_key}/{book["abbreviation"]}/(\\d+)\\?lang=eng'

            match = re.search(pattern, href)
            if match:
                chapter_num = int(match.group(1))
                chapters.append({
                    'number': chapter_num,
                    'url': self.base_url + href
                })

        # Sort by chapter number
        chapters.sort(key=lambda x: x['number'])

        logger.info(f"Discovered {len(chapters)} chapters in {book['name']}")
        return chapters

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

    def extract_chapter_content(self, html, url):
        """Extract chapter content from HTML."""
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

    def format_chapter_file(self, collection_name, book_name, chapter_num, content, is_section=False):
        """Format chapter content for file output."""
        chapter_label = "Section" if is_section else "Chapter"

        lines = [
            f"Collection: {collection_name}",
            f"Book: {book_name}",
            f"{chapter_label}: {chapter_num}",
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

    def save_chapter(self, collection_key, book_name, chapter_num, content):
        """Save chapter content to file."""
        collection = self.collections[collection_key]
        collection_name = collection['name']

        # Determine if this is a section (D&C) or chapter
        is_section = collection_key == 'dc-testament'
        chapter_label = "Section" if is_section else "Chapter"

        filename = f"[{collection_name}][{book_name}][{chapter_label} {chapter_num}].md"
        output_dir = self.base_dir / collection['directory']
        filepath = output_dir / filename

        formatted_content = self.format_chapter_file(
            collection_name, book_name, chapter_num, content, is_section
        )

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False

    def scrape_chapter(self, collection_key, book_name, chapter_info):
        """Scrape a single chapter."""
        html = self.fetch_page(chapter_info['url'])
        if not html:
            return False

        content = self.extract_chapter_content(html, chapter_info['url'])
        if not content['verses']:
            logger.warning(f"No verses found for {book_name} Chapter {chapter_info['number']}")
            return False

        return self.save_chapter(collection_key, book_name, chapter_info['number'], content)

    def scrape_collection(self, collection_key):
        """Scrape an entire collection."""
        collection = self.collections[collection_key]
        logger.info(f"Starting {collection['name']} scraping...")

        books = self.discover_books(collection_key)
        if not books:
            logger.error(f"No books found for {collection['name']}")
            return

        collection_stats = {'books': len(books), 'chapters': 0, 'completed': 0, 'failed': 0}

        for book in books:
            logger.info(f"Scraping {book['name']}...")

            chapters = self.discover_chapters(collection_key, book)
            collection_stats['chapters'] += len(chapters)

            for chapter in chapters:
                if self.scrape_chapter(collection_key, book['name'], chapter):
                    collection_stats['completed'] += 1
                    self.progress['completed'] += 1
                else:
                    collection_stats['failed'] += 1
                    self.progress['failed'] += 1

                # Progress update
                total_processed = self.progress['completed'] + self.progress['failed']
                if self.progress['total_files'] > 0:
                    percent = (total_processed / self.progress['total_files']) * 100
                    logger.info(f"Overall progress: {total_processed}/{self.progress['total_files']} ({percent:.1f}%)")

        self.progress['collections'][collection_key] = collection_stats
        logger.info(f"{collection['name']} complete: {collection_stats['completed']} success, {collection_stats['failed']} failed")

    def estimate_total_files(self):
        """Estimate total files for progress tracking."""
        estimates = {
            'ot': 929,      # Old Testament
            'nt': 260,      # New Testament
            'bofm': 239,    # Book of Mormon
            'dc-testament': 140  # D&C (138 sections + 2 Official Declarations)
        }

        self.progress['total_files'] = sum(estimates.values())
        logger.info(f"Estimated total files to scrape: {self.progress['total_files']}")

    def scrape_all(self, collections_to_scrape=None):
        """Scrape all collections or specified ones."""
        if collections_to_scrape is None:
            collections_to_scrape = list(self.collections.keys())

        self.estimate_total_files()

        logger.info("Starting comprehensive scripture scraping...")
        start_time = time.time()

        for collection_key in collections_to_scrape:
            if collection_key in self.collections:
                self.scrape_collection(collection_key)
            else:
                logger.error(f"Unknown collection: {collection_key}")

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Scraping complete!")
        logger.info(f"Total time: {duration/60:.1f} minutes")
        logger.info(f"Files completed: {self.progress['completed']}")
        logger.info(f"Files failed: {self.progress['failed']}")

        return self.progress

def main():
    scraper = ScriptureScraper()

    # You can specify which collections to scrape:
    # scraper.scrape_all(['dc-testament'])  # Just D&C
    # scraper.scrape_all(['nt', 'bofm'])   # Just NT and BoM

    # Or scrape everything:
    progress = scraper.scrape_all()

    print(f"\n{'='*60}")
    print("FINAL SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully scraped: {progress['completed']} files")
    print(f"Failed: {progress['failed']} files")
    print(f"Total estimated: {progress['total_files']} files")

    for collection_key, stats in progress['collections'].items():
        collection_name = scraper.collections[collection_key]['name']
        print(f"\n{collection_name}:")
        print(f"  Books: {stats['books']}")
        print(f"  Chapters: {stats['chapters']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Failed: {stats['failed']}")

if __name__ == "__main__":
    main()