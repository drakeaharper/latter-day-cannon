#!/usr/bin/env python3
"""
Follow Him Podcast Scraper

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2025 Doctrine & Covenants year and saves them as markdown files.
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
        logging.FileHandler('followhim_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_url, part2_url, favorites_url)
EPISODES = [
    # Episodes 1-10
    (1, "The Restoration of the Gospel of Jesus Christ", "3-19", "2-372", "2-371"),
    (2, "D&C 1", "2-375", "2-374", "2-373"),
    (3, "Joseph Smith History 1:1-26", "2-378", "2-377", "2-376"),
    (4, "D&C 2; Joseph Smith History 1:27-65", "2-381", "2-380", "2-379"),
    (5, "D&C 3-5", "2-384", "2-383", "2-382"),
    (6, "D&C 6-9", "2-387", "2-386", "2-385"),
    (7, "D&C 10-11", "2-390", "2-389", "2-388"),
    (8, "D&C 12-17; Joseph Smith History 1:66-75", "2-393", "2-392", "2-391"),
    (9, "D&C 18", "2-396", "2-395", "2-394"),
    (10, "D&C 19", "2-399", "2-398", "2-397"),
    # Episodes 11-20
    (11, "D&C 20-22", "2-402", "2-401", "2-400"),
    (12, "D&C 23-26", "2-405", "2-404", "2-403"),
    (13, "D&C 27-28", "2-408", "2-407", "2-406"),
    (14, "D&C 29", "2-411", "2-410", "2-409"),
    (15, "D&C 30-36", "2-414", "2-413", "2-409"),  # Note: Favorites might be duplicate
    (16, "Easter", "2-417", "2-416", "2-415"),
    (17, "D&C 37-40", "2-420", "2-419", "2-418"),
    (18, "D&C 41-44", "2-423", "2-422", "2-421"),
    (19, "D&C 45", "2-426", "2-425", "2-424"),
    (20, "D&C 46-48", "2-428", "3-20", "2-427"),
    # Episodes 21-30
    (21, "D&C 49-50", "2-431", "2-430", "2-429"),
    (22, "D&C 51-57", "2-440", "2-439", "2-438"),
    (23, "D&C 58-59", "doctrine-covenants-episode-23-2025-doctrine-covenants-58-59-part-1", "doctrine-covenants-episode-23-2025-doctrine-covenants-58-59-part-2", "doctrine-covenants-episode-23-2025-doctrine-covenants-58-59-favorites"),
    (24, "D&C 60-63", "doctrine-covenants-episode-24-2025-doctrine-covenants-60-63-part-1", "doctrine-covenants-episode-24-2025-doctrine-covenants-60-63-part-2", "doctrine-covenants-episode-24-2025-doctrine-covenants-60-63-favorites"),
    (25, "D&C 64-66", "2-443", "2-442", "2-441"),
    (26, "D&C 67-70", "2-444", "2-446", "2-445"),
    (27, "D&C 71-75", "2-448", "3-28", "2-447"),
    (28, "D&C 76", "2-451", "2-450", "2-449"),
    (29, "D&C 77-80", "2-454", "2-452", "2-453"),
    (30, "D&C 81-83", "2-456", "2-457", "2-458"),
    # Episodes 31-40
    (31, "D&C 84", "2-459", "2-460", "2-461"),
    (32, "D&C 85-87", "2-464", "2-463", "2-462"),
    (33, "D&C 88", "2-467", "2-466", "2-465"),
    (34, "D&C 89-92", "2-468", "2-469", "2-470"),
    (35, "D&C 93", "2-473", "2-472", "2-471"),
    (36, "D&C 94-97", "2-476", "2-475", "2-474"),
    (37, "D&C 98-101", "2-479", "2-478", "2-477"),
    (38, "D&C 102-105", "2-482", "2-481", "2-480"),
    (39, "D&C 106-108", "2-486", "2-485", "2-484"),
    (40, "D&C 109-110", "2-489", "2-488", "2-487"),
    # Episodes 41-49
    (41, "D&C 111-114", "2-493", "2-492", "2-491"),
    (42, "D&C 115-120", "2-494", "2-495", "2-496"),
    (43, "D&C 121-123", "2-499", "2-498", "2-497"),
    (44, "D&C 124", "2-501", "2-502", "2-503"),
    (45, "D&C 125-128", "2-505", "2-506", "2-507"),
    (46, "D&C 129-132", "2-510", "2-509", "2-508"),
    (47, "D&C 133-134", "2-514", "2-513", "2-512"),
    (48, "D&C 135-136", "2-517", "2-516", "2-515"),
    (49, "D&C 137-138", "2-520", "2-518", "2-519"),
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/doctrine-and-covenants-2025"):
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

    def extract_show_notes(self, url):
        """Extract content from a show notes page"""
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
        guest = None
        guest_pattern = re.compile(r'(?:Dr\.|Brother|Sister|Elder)\s+[A-Z][a-z]+\s+[A-Z][a-z]+')

        # Extract main content - look for article or main content area
        content_area = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('main')

        if not content_area:
            # Fallback: look for the largest text block
            content_area = soup.find('body')

        if not content_area:
            logging.warning(f"No content found for {url}")
            return None

        # Extract all text content
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
                # Check for guest name
                if not guest:
                    match = guest_pattern.search(text)
                    if match:
                        guest = match.group()
                transcript_lines.append(text)

        transcript = '\n\n'.join(transcript_lines)

        # Try to extract timestamps if present
        timestamps = re.findall(r'\b(\d{1,2}:\d{2}(?::\d{2})?)\b', transcript)

        return {
            'title': title,
            'url': url,
            'guest': guest,
            'transcript': transcript,
            'has_timestamps': len(timestamps) > 0
        }

    def save_show_notes(self, episode_num, topic, part_type, data):
        """Save show notes data as markdown file"""
        if not data:
            return False

        # Create filename: [Episode XX][Topic][Part].md
        safe_topic = re.sub(r'[<>:"/\\|?*;]', '', topic)
        filename = f"[Episode {episode_num:02d}][{safe_topic}][{part_type}].md"
        filepath = self.output_dir / filename

        # Build markdown content
        content = f"Episode: {episode_num}\n"
        content += f"Topic: {topic}\n"
        content += f"Part: {part_type}\n"
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

    def scrape_episode(self, episode_num, topic, part1_slug, part2_slug, favorites_slug):
        """Scrape all parts of a single episode"""
        results = {'part1': False, 'part2': False, 'favorites': False}

        # Scrape Part 1
        logging.info(f"[Episode {episode_num}] Scraping Part 1...")
        url = self.build_url(part1_slug)
        data = self.extract_show_notes(url)
        if data:
            results['part1'] = self.save_show_notes(episode_num, topic, "Part 1", data)
        time.sleep(2)

        # Scrape Part 2
        logging.info(f"[Episode {episode_num}] Scraping Part 2...")
        url = self.build_url(part2_slug)
        data = self.extract_show_notes(url)
        if data:
            results['part2'] = self.save_show_notes(episode_num, topic, "Part 2", data)
        time.sleep(2)

        # Scrape Favorites
        logging.info(f"[Episode {episode_num}] Scraping Favorites...")
        url = self.build_url(favorites_slug)
        data = self.extract_show_notes(url)
        if data:
            results['favorites'] = self.save_show_notes(episode_num, topic, "Favorites", data)
        time.sleep(2)

        return results

    def scrape_all(self):
        """Scrape all episodes"""
        logging.info("Starting Follow Him podcast scraping...")
        logging.info(f"Total episodes to scrape: {len(EPISODES)}")
        logging.info(f"Total files to create: {len(EPISODES) * 3}")

        successful = 0
        failed = 0

        for episode in EPISODES:
            episode_num, topic, part1, part2, favorites = episode
            logging.info(f"\n[{episode_num}/{len(EPISODES)}] Processing: Episode {episode_num} - {topic}")

            try:
                results = self.scrape_episode(episode_num, topic, part1, part2, favorites)
                successful += sum(results.values())
                failed += 3 - sum(results.values())
            except Exception as e:
                logging.error(f"Error processing Episode {episode_num}: {e}")
                failed += 3

        logging.info(f"\n{'='*50}")
        logging.info(f"Scraping complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"Total attempted: {len(EPISODES) * 3}")


def main():
    scraper = FollowHimScraper()
    scraper.scrape_all()


if __name__ == "__main__":
    main()
