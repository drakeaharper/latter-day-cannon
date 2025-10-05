#!/usr/bin/env python3
"""
Focused scraper for Doctrine and Covenants
Tests the comprehensive approach on a smaller collection first
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
        logging.FileHandler('dc_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DCScraper:
    def __init__(self):
        self.base_url = "https://www.churchofjesuschrist.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.output_dir = Path("scriptures/doctrine-and-covenants")
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def discover_sections(self):
        """Discover all sections in D&C."""
        # We know D&C has sections 1-138 plus Official Declarations
        sections = []

        # Add regular sections 1-138
        for i in range(1, 139):
            sections.append({
                'number': i,
                'type': 'section',
                'url': f"{self.base_url}/study/scriptures/dc-testament/dc/{i}?lang=eng"
            })

        # Add Official Declarations
        sections.extend([
            {
                'number': 1,
                'type': 'od',
                'url': f"{self.base_url}/study/scriptures/dc-testament/od/1?lang=eng"
            },
            {
                'number': 2,
                'type': 'od',
                'url': f"{self.base_url}/study/scriptures/dc-testament/od/2?lang=eng"
            }
        ])

        logger.info(f"Prepared {len(sections)} sections/declarations to scrape")
        return sections

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

    def format_file(self, section_info, content):
        """Format content for file output."""
        if section_info['type'] == 'od':
            section_label = f"Official Declaration {section_info['number']}"
            book_name = "Official Declarations"
        else:
            section_label = f"Section {section_info['number']}"
            book_name = "Doctrine and Covenants"

        lines = [
            f"Collection: Doctrine and Covenants",
            f"Book: {book_name}",
            f"Section: {section_info['number']}",
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

    def save_section(self, section_info, content):
        """Save section content to file."""
        if section_info['type'] == 'od':
            filename = f"[Doctrine and Covenants][Official Declarations][Official Declaration {section_info['number']}].md"
        else:
            filename = f"[Doctrine and Covenants][Doctrine and Covenants][Section {section_info['number']}].md"

        filepath = self.output_dir / filename
        formatted_content = self.format_file(section_info, content)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False

    def scrape_section(self, section_info):
        """Scrape a single section."""
        html = self.fetch_page(section_info['url'])
        if not html:
            return False

        content = self.extract_content(html, section_info['url'])
        if not content['verses']:
            logger.warning(f"No verses found for {section_info}")
            return False

        return self.save_section(section_info, content)

    def scrape_all(self):
        """Scrape all D&C sections."""
        logger.info("Starting Doctrine and Covenants scraping...")

        sections = self.discover_sections()
        completed = 0
        failed = 0

        for i, section in enumerate(sections, 1):
            if self.scrape_section(section):
                completed += 1
            else:
                failed += 1

            logger.info(f"Progress: {i}/{len(sections)} sections processed")

        logger.info(f"D&C scraping complete! {completed} successful, {failed} failed")
        return completed, failed

def main():
    scraper = DCScraper()
    completed, failed = scraper.scrape_all()

    print(f"\nDoctrine and Covenants Scraping Summary:")
    print(f"Successfully scraped: {completed} sections")
    print(f"Failed: {failed} sections")
    print(f"Output directory: {scraper.output_dir}")

if __name__ == "__main__":
    main()