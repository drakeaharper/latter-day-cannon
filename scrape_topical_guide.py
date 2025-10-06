#!/usr/bin/env python3
"""
Topical Guide Scraper for LDS Scripture Study Helps

Scrapes all topics from the LDS Topical Guide and saves them as markdown files.
Each topic includes cross-references and scripture references organized by collection.
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
        logging.FileHandler('topical_guide_scraping.log'),
        logging.StreamHandler()
    ]
)

class TopicalGuideScraper:
    """Scraper for LDS Topical Guide"""

    BASE_URL = "https://www.churchofjesuschrist.org"
    INDEX_URL = f"{BASE_URL}/study/scriptures/tg?lang=eng"

    def __init__(self, output_dir="study_helps/topical_guide"):
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

    def discover_topics(self):
        """Discover all topics from the index page"""
        logging.info("Discovering topics from index page...")
        html = self.fetch_page(self.INDEX_URL)
        if not html:
            logging.error("Failed to fetch index page")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        topics = []

        # Find all links to topic pages
        # Pattern: /study/scriptures/tg/[topic-slug]?lang=eng
        links = soup.find_all('a', href=re.compile(r'/study/scriptures/tg/[^/?]+\?lang=eng'))

        for link in links:
            href = link.get('href')
            # Skip introduction and contents pages
            if 'introduction' in href or href.endswith('/tg?lang=eng'):
                continue

            # Extract topic name from the link text
            topic_title = link.get_text(strip=True)
            if topic_title:
                full_url = self.BASE_URL + href if href.startswith('/') else href
                topics.append((topic_title, full_url))

        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic, url in topics:
            if url not in seen:
                seen.add(url)
                unique_topics.append((topic, url))

        logging.info(f"Discovered {len(unique_topics)} unique topics")
        return unique_topics

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def extract_topic_content(self, url):
        """Extract content from a topic page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract topic title
        title_elem = soup.find('h1')
        if not title_elem:
            # Try alternative selectors
            title_elem = soup.find('title')

        topic_title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown Topic"

        # Extract main body content
        body = soup.find('div', class_='body')
        if not body:
            logging.warning(f"No body content found for {url}")
            return None

        # Extract "See Also" section
        see_also = []
        paragraphs = body.find_all('p')

        # First paragraph typically contains "See also" references
        if paragraphs:
            first_p_text = paragraphs[0].get_text()
            if 'See also' in first_p_text:
                # Extract links from the first paragraph
                links = paragraphs[0].find_all('a')
                for link in links:
                    link_text = self.clean_text(link.get_text())
                    if link_text and not link_text.startswith('BD'):
                        see_also.append(link_text)

        # Extract scripture references
        references = {
            'Old Testament': [],
            'New Testament': [],
            'Book of Mormon': [],
            'Doctrine and Covenants': [],
            'Pearl of Great Price': []
        }

        # Process each paragraph (skip first if it's "See also")
        start_idx = 1 if see_also else 0

        for p in paragraphs[start_idx:]:
            text = self.clean_text(p.get_text())
            if not text:
                continue

            # Determine collection based on book abbreviation in the text
            collection = None

            # New Testament books
            if any(book in text for book in ['Matt.', 'Mark', 'Luke', 'John', 'Acts', 'Rom.', '1 Cor.', '2 Cor.', 'Gal.', 'Eph.', 'Phil.', 'Col.', '1 Thes.', '2 Thes.', '1 Tim.', '2 Tim.', 'Titus', 'Philem.', 'Heb.', 'James', '1 Pet.', '2 Pet.', '1 Jn.', '2 Jn.', '3 Jn.', 'Jude', 'Rev.']):
                collection = 'New Testament'

            # Old Testament books
            elif any(book in text for book in ['Gen.', 'Ex.', 'Lev.', 'Num.', 'Deut.', 'Josh.', 'Judg.', 'Ruth', '1 Sam.', '2 Sam.', '1 Kgs.', '2 Kgs.', '1 Chr.', '2 Chr.', 'Ezra', 'Neh.', 'Esth.', 'Job', 'Ps.', 'Prov.', 'Eccl.', 'Song.', 'Isa.', 'Jer.', 'Lam.', 'Ezek.', 'Dan.', 'Hosea', 'Joel', 'Amos', 'Obad.', 'Jonah', 'Micah', 'Nahum', 'Hab.', 'Zeph.', 'Hag.', 'Zech.', 'Mal.']):
                collection = 'Old Testament'

            # Book of Mormon books
            elif any(book in text for book in ['1 Ne.', '2 Ne.', 'Jacob', 'Enos', 'Jarom', 'Omni', 'W of M', 'Mosiah', 'Alma', 'Hel.', '3 Ne.', '4 Ne.', 'Morm.', 'Ether', 'Moro.']):
                collection = 'Book of Mormon'

            # Doctrine and Covenants
            elif 'D&C' in text:
                collection = 'Doctrine and Covenants'

            # Pearl of Great Price
            elif any(book in text for book in ['Moses', 'Abr.', 'JS—M', 'JS—H', 'A of F']):
                collection = 'Pearl of Great Price'

            if collection:
                references[collection].append(text)

        return {
            'title': topic_title,
            'url': url,
            'see_also': see_also,
            'references': references
        }

    def save_topic(self, topic_data):
        """Save topic data as markdown file"""
        if not topic_data:
            return

        # Create filename from topic title
        filename = f"{topic_data['title']}.md"
        # Clean filename of invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filepath = self.output_dir / filename

        # Build markdown content
        content = f"Topic: {topic_data['title']}\n"
        content += f"URL: {topic_data['url']}\n\n"
        content += "---\n\n"

        # Add "See Also" section
        if topic_data['see_also']:
            content += "## See Also\n\n"
            content += '; '.join(topic_data['see_also']) + "\n\n"
            content += "---\n\n"

        # Add scripture references by collection
        for collection in ['Old Testament', 'New Testament', 'Book of Mormon', 'Doctrine and Covenants', 'Pearl of Great Price']:
            refs = topic_data['references'].get(collection, [])
            if refs:
                content += f"## {collection}\n\n"
                for ref in refs:
                    content += f"- {ref}\n"
                content += "\n"

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename}")
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")

    def scrape_all(self):
        """Scrape all topics"""
        logging.info("Starting Topical Guide scraping...")

        # Discover all topics
        topics = self.discover_topics()
        if not topics:
            logging.error("No topics discovered")
            return

        logging.info(f"Found {len(topics)} topics to scrape")

        # Scrape each topic
        successful = 0
        failed = 0

        for i, (topic_title, url) in enumerate(topics, 1):
            logging.info(f"[{i}/{len(topics)}] Processing: {topic_title}")

            try:
                topic_data = self.extract_topic_content(url)
                if topic_data:
                    self.save_topic(topic_data)
                    successful += 1
                else:
                    logging.warning(f"Failed to extract content for: {topic_title}")
                    failed += 1
            except Exception as e:
                logging.error(f"Error processing {topic_title}: {e}")
                failed += 1

            # Rate limiting
            time.sleep(2)

        logging.info(f"\nScraping complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"Total: {len(topics)}")

def main():
    scraper = TopicalGuideScraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()
