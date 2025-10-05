#!/usr/bin/env python3
"""
Old Testament scraper
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from pathlib import Path
import re

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
        for attempt in range(max_retries):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                time.sleep(2)
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

    def clean_verse_text(self, verse_element):
        verse_copy = verse_element.__copy__()
        verse_num_span = verse_copy.find('span', class_='verse-number')
        if verse_num_span:
            verse_num = verse_num_span.get_text().strip()
            verse_num_span.decompose()
        else:
            verse_num = ""

        for note_ref in verse_copy.find_all('a', class_='study-note-ref'):
            note_ref.replace_with(note_ref.get_text())

        for sup in verse_copy.find_all('sup'):
            sup.decompose()

        verse_text = verse_copy.get_text().strip()
        verse_text = re.sub(r'\s+', ' ', verse_text)
        return verse_num, verse_text

    def extract_content(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        title_element = soup.find('h1')
        title = title_element.get_text().strip() if title_element else ""
        summary_element = soup.find('p', class_='study-summary')
        summary = summary_element.get_text().strip() if summary_element else ""

        verses = []
        verse_elements = soup.find_all('p', class_='verse')
        for verse_element in verse_elements:
            verse_num, verse_text = self.clean_verse_text(verse_element)
            if verse_text:
                verses.append((verse_num, verse_text))

        return {'title': title, 'summary': summary, 'verses': verses, 'url': url}

    def save_chapter(self, book_name, chapter_num, content):
        filename = f"[Old Testament][{book_name}][Chapter {chapter_num}].md"
        filepath = self.output_dir / filename

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

        if content['summary']:
            lines.extend([content['summary'], ""])

        for verse_num, verse_text in content['verses']:
            if verse_num:
                lines.append(f"{verse_num} {verse_text}")
            else:
                lines.append(verse_text)
            lines.append("")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False

    def scrape_all(self):
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
                url = f"{self.base_url}/study/scriptures/ot/{book_abbr}/{chapter}?lang=eng"
                html = self.fetch_page(url)
                if html:
                    content = self.extract_content(html, url)
                    if content['verses'] and self.save_chapter(book_name, chapter, content):
                        completed += 1
                    else:
                        failed += 1
                else:
                    failed += 1

                processed += 1
                if processed % 10 == 0:  # Log every 10 to reduce spam
                    logger.info(f"Progress: {processed}/{total_chapters} ({processed/total_chapters*100:.1f}%)")

        logger.info(f"Old Testament complete! {completed} successful, {failed} failed")
        return completed, failed

if __name__ == "__main__":
    scraper = OTScraper()
    scraper.scrape_all()