#!/usr/bin/env python3
"""
Follow Him: Voices of the Restoration Scraper

Scrapes all episodes from the Voices of the Restoration series
(behind-the-scenes history of Doctrine & Covenants) and saves as markdown files.
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
        logging.FileHandler('followhim_voices_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, title, show_note_slug)
# Voices of the Restoration is a single-part series (no Part 1/Part 2/Favorites)
EPISODES = [
    (1, "Joseph Smith's Family", "2-432"),
    (2, "Translation of the Book of Mormon", "2-433"),
    (3, "The Witnesses of the Book of Mormon", "2-434"),
    (4, "Emma Hale Smith", "2-435"),
    (5, "Early Converts", "2-436"),
    (6, "Gathering to Ohio", "2-437"),
    (7, "Testimonies of 'The Vision'", "2-455"),
    (8, "Zion's Camp", "2-483"),
    (9, "Spiritual Manifestations and the Kirtland Temple", "2-490"),
    (10, "Liberty Jail", "2-500"),
    (11, "The Relief Society", "2-504"),
    (12, "Baptism for Our Ancestors, 'a Glorious Doctrine'", "2-511"),
]


class VoicesOfRestorationScraper:
    """Scraper for Follow Him: Voices of the Restoration podcast"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/voices-of-the-restoration"):
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

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Normalize whitespace but preserve paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text

    def extract_episode_content(self, url):
        """Extract content from an episode page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract title from h1 or title tag
        title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find('title')
        title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown Title"

        # Try to extract guest name from the content
        guest = "Dr. Gerrit Dirkmaat"  # Default guest for this series

        # Extract main content - look for article or main content area
        content_area = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('main')

        if not content_area:
            # Fallback: look for the largest text block
            content_area = soup.find('body')

        if not content_area:
            logging.warning(f"No content found for {url}")
            return None

        # Remove script and style elements
        for script in content_area(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        # Get all paragraphs
        paragraphs = content_area.find_all(['p', 'h2', 'h3', 'h4'])

        # Build transcript text
        transcript_lines = []
        for elem in paragraphs:
            text = self.clean_text(elem.get_text())
            if text and len(text) > 10:  # Skip very short lines
                transcript_lines.append(text)

        transcript = '\n\n'.join(transcript_lines)

        return {
            'title': title,
            'url': url,
            'guest': guest,
            'transcript': transcript,
        }

    def save_episode(self, episode_num, topic, data):
        """Save episode data as markdown file"""
        if not data:
            return False

        # Create filename: [Episode XX][Topic].md
        safe_topic = re.sub(r'[<>:"/\\|?*;]', '', topic)
        filename = f"[Episode {episode_num:02d}][{safe_topic}].md"
        filepath = self.output_dir / filename

        # Build markdown content
        content = f"Episode: {episode_num}\n"
        content += f"Series: Voices of the Restoration\n"
        content += f"Topic: {topic}\n"
        if data.get('guest'):
            content += f"Guest: {data['guest']}\n"
        content += f"URL: {data['url']}\n\n"
        content += "---\n\n"

        # Add title
        content += f"# {data['title']}\n\n"

        # Add transcript
        content += data['transcript']
        content += "\n"

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")
            return False

    def build_url(self, slug):
        """Build full URL from slug"""
        return f"{self.BASE_URL}/show-note/{slug}/"

    def scrape_episode(self, episode_num, topic, slug):
        """Scrape a single episode"""
        logging.info(f"[Episode {episode_num}] Scraping: {topic}")
        url = self.build_url(slug)
        data = self.extract_episode_content(url)
        if data:
            return self.save_episode(episode_num, topic, data)
        return False

    def scrape_all(self):
        """Scrape all episodes"""
        logging.info("Starting Voices of the Restoration scraping...")
        logging.info(f"Total episodes to scrape: {len(EPISODES)}")

        successful = 0
        failed = 0

        for episode_num, topic, slug in EPISODES:
            logging.info(f"\n[{episode_num}/{len(EPISODES)}] Processing: Episode {episode_num} - {topic}")

            try:
                if self.scrape_episode(episode_num, topic, slug):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Error processing Episode {episode_num}: {e}")
                failed += 1

            time.sleep(2)  # Rate limiting

        logging.info(f"\n{'='*50}")
        logging.info(f"Scraping complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"Total attempted: {len(EPISODES)}")


def main():
    scraper = VoicesOfRestorationScraper()
    scraper.scrape_all()


if __name__ == "__main__":
    main()
