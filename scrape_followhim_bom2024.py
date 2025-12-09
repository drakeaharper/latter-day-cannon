#!/usr/bin/env python3
"""
Follow Him Podcast Scraper - Book of Mormon 2024

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2024 Book of Mormon year and saves them as markdown files.
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
        logging.FileHandler('followhim_bom2024_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_slug, part2_slug, favorites_slug)
# Using full URL slugs since 2024 uses descriptive URLs
EPISODES = [
    # Episodes 1-10
    (1, "Introductory Pages of the Book of Mormon",
     "book-of-mormon-episode-01-introductory-pages-of-the-book-of-mormon-part-1",
     "book-of-mormon-episode-01-introductory-pages-of-the-book-of-mormon-part-2",
     "book-of-mormon-episode-01-introductory-pages-of-the-book-of-mormon-favorites"),
    (2, "1 Nephi 1-5",
     "book-of-mormon-episode-02-1-nephi-1-5-part-1",
     "book-of-mormon-episode-02-1-nephi-1-5-part-2",
     "book-of-mormon-episode-02-1-nephi-1-5-favorites"),
    (3, "1 Nephi 6-10",
     "book-of-mormon-episode-03-1-nephi-6-10-part-1",
     "book-of-mormon-episode-03-1-nephi-6-10-part-2",
     "book-of-mormon-episode-03-1-nephi-6-10-favorites"),
    (4, "1 Nephi 11-15",
     "book-of-mormon-episode-04-1-nephi-11-15-part-1",
     "book-of-mormon-episode-04-1-nephi-11-15-part-2",
     "book-of-mormon-episode-04-1-nephi-11-15-favorites"),
    (5, "1 Nephi 16-22",
     "book-of-mormon-episode-05-1-nephi-16-22-part-1",
     "book-of-mormon-episode-05-1-nephi-16-22-part-2",
     "book-of-mormon-episode-05-1-nephi-16-22-favorites"),
    (6, "2 Nephi 1-2",
     "book-of-mormon-episode-06-2-nephi-1-2-part-1",
     "book-of-mormon-episode-06-2-nephi-1-2-part-2",
     "book-of-mormon-episode-06-2-nephi-1-2-favorites"),
    (7, "2 Nephi 3-5",
     "book-of-mormon-episode-07-2-nephi-3-5-part-1",
     "book-of-mormon-episode-07-2-nephi-3-5-part-2",
     "book-of-mormon-episode-07-2-nephi-3-5-favorites"),
    (8, "2 Nephi 6-10",
     "book-of-mormon-episode-08-2-nephi-6-10-part-1",
     "book-of-mormon-episode-08-2-nephi-6-10-part-2",
     "book-of-mormon-episode-08-2-nephi-6-10-favorites"),
    (9, "2 Nephi 11-19",
     "book-of-mormon-episode-09-2-nephi-11-19-part-1",
     "book-of-mormon-episode-09-2-nephi-11-19-part-2",
     "book-of-mormon-episode-09-2-nephi-11-19-favorites"),
    (10, "2 Nephi 20-25",
     "book-of-mormon-episode-10-2-nephi-20-25-part-1",
     "book-of-mormon-episode-10-2-nephi-20-25-part-2",
     "book-of-mormon-episode-10-2-nephi-20-25-favorites"),
    # Episodes 11-20
    (11, "2 Nephi 26-30",
     "book-of-mormon-episode-11-2-nephi-26-30-part-1",
     "book-of-mormon-episode-11-2-nephi-26-30-part-2",
     "book-of-mormon-episode-11-2-nephi-26-30-favorites"),
    (12, "2 Nephi 31-33",
     "book-of-mormon-episode-12-2-nephi-31-33-part-1",
     "book-of-mormon-episode-12-2-nephi-31-33-part-2",
     "book-of-mormon-episode-12-2-nephi-31-33-favorites"),
    (13, "Easter",
     "book-of-mormon-episode-13-easter-part-1",
     "book-of-mormon-episode-13-easter-part-2",
     "book-of-mormon-episode-13-easter-favorites"),
    (14, "Jacob 1-4",
     "book-of-mormon-episode-14-jacob-1-4-part-1",
     "book-of-mormon-episode-14-jacob-1-4-part-2",
     "book-of-mormon-episode-14-jacob-1-4-favorites"),
    (15, "Jacob 5-7",
     "book-of-mormon-episode-15-jacob-5-7-part-1",
     "book-of-mormon-episode-15-jacob-5-7-part-2",
     "book-of-mormon-episode-15-jacob-5-7-favorites"),
    (16, "Enos - Words of Mormon",
     "book-of-mormon-episode-16-enos-words-of-mormon-part-1",
     "book-of-mormon-episode-16-enos-words-of-mormon-part-2",
     "book-of-mormon-episode-16-enos-word-of-mormon-favorites"),
    (17, "Mosiah 1-3",
     "book-of-mormon-episode-17-mosiah-1-3-part-1",
     "book-of-mormon-episode-17-mosiah-1-3-part-2",
     "book-of-mormon-episode-17-mosiah-1-3-favorites"),
    (18, "Mosiah 4-6",
     "book-of-mormon-episode-18-mosiah-4-6-part-1",
     "book-of-mormon-episode-18-mosiah-4-6-part-2",
     "book-of-mormon-episode-18-mosiah-4-6-favorites"),
    (19, "Mosiah 7-10",
     "book-of-mormon-episode-19-mosiah-7-10-part-1",
     "book-of-mormon-episode-19-mosiah-7-10-part-2",
     "book-of-mormon-episode-19-mosiah-7-10-favorites"),
    (20, "Mosiah 11-17",
     "book-of-mormon-episode-20-mosiah-11-17-part-1",
     "book-of-mormon-episode-20-mosiah-11-17-part-2",
     "book-of-mormon-episode-20-mosiah-11-17-favorites"),
    # Episodes 21-30
    (21, "Mosiah 18-24",
     "book-of-mormon-episode-21-mosiah-18-24-part-1",
     "book-of-mormon-episode-21-mosiah-18-24-part-2",
     "book-of-mormon-episode-21-mosiah-18-24-favorites"),
    (22, "Mosiah 25-28",
     "book-of-mormon-episode-22-mosiah-25-28-part-1",
     "book-of-mormon-episode-22-mosiah-25-28-part-2",
     "3-21"),  # Favorites uses numeric slug
    (23, "Mosiah 29 - Alma 4",
     "book-of-mormon-episode-23-mosiah-29-alma-4-part-1",
     "book-of-mormon-episode-23-mosiah-29-alma-4-part-2",
     "book-of-mormon-episode-23-mosiah-29-alma-4-favorites"),
    (24, "Alma 5-7",
     "book-of-mormon-episode-24-alma-5-7-part-1",
     "book-of-mormon-episode-24-alma-5-7-part-2",
     "book-of-mormon-episode-24-alma-5-7-favorites"),
    (25, "Alma 8-12",
     "book-of-mormon-episode-25-alma-8-12-part-1",
     "book-of-mormon-episode-25-alma-8-12-part-2",
     "book-of-mormon-episode-25-alma-8-12-favorites"),
    (26, "Alma 13-16",
     "book-of-mormon-episode-26-alma-13-16-part-1",
     "book-of-mormon-episode-26-alma-13-16-part-2",
     "book-of-mormon-episode-26-alma-13-16-favorites"),
    (27, "Alma 17-22",
     "book-of-mormon-episode-27-alma-17-22-part-1",
     "book-of-mormon-episode-27-alma-17-22-part-2",
     "3-22"),  # Favorites uses numeric slug
    (28, "Alma 23-29",
     "book-of-mormon-episode-28-alma-23-29-part-1",
     "book-of-mormon-episode-28-alma-23-29-part-2",
     "book-of-mormon-episode-28-alma-23-29-favorites"),
    (29, "Alma 30-31",
     "book-of-mormon-episode-29-alma-30-31-part-1",
     "book-of-mormon-episode-29-alma-30-31-part-2",
     "book-of-mormon-episode-29-alma-30-31-favorites"),
    (30, "Alma 32-35",
     "book-of-mormon-episode-30-alma-32-35-part-1",
     "book-of-mormon-episode-30-alma-32-35-part-2",
     "book-of-mormon-episode-30-alma-32-35-favorites"),
    # Episodes 31-40
    (31, "Alma 36-38",
     "book-of-mormon-episode-31-alma-36-38-part-1",
     "book-of-mormon-episode-31-alma-36-38-part-2",
     "book-of-mormon-episode-31-alma-36-38-favorites"),
    (32, "Alma 39-42",
     "book-of-mormon-episode-32-alma-39-42-part-1",
     "book-of-mormon-episode-32-alma-39-42-part-2",
     "book-of-mormon-episode-32-alma-39-42-favorites"),
    (33, "Alma 43-52",
     "book-of-mormon-episode-33-alma-43-52-part-1",
     "book-of-mormon-episode-33-alma-43-52-part-2",
     "book-of-mormon-episode-33-alma-43-52-favorites"),
    (34, "Alma 53-63",
     "book-of-mormon-episode-34-alma-53-63-part-1",
     "book-of-mormon-episode-34-alma-53-63-part-2",
     "book-of-mormon-episode-34-alma-53-63-favorites"),
    (35, "Helaman 1-6",
     "book-of-mormon-episode-35-helaman-1-6-part-1",
     "book-of-mormon-episode-35-helaman-1-6-part-2",
     "3-23"),  # Favorites uses numeric slug
    (36, "Helaman 7-12",
     "book-of-mormon-episode-36-helaman-7-12-part-1",
     "book-of-mormon-episode-36-helaman-7-12-part-2",
     "book-of-mormon-episode-36-helaman-7-12-favorites"),
    (37, "Helaman 13-16",
     "book-of-mormon-episode-37-helaman-13-16-part-1",
     "book-of-mormon-episode-37-helaman-13-16-part-2",
     "book-of-mormon-episode-37-helaman-13-16-favorites"),
    (38, "3 Nephi 1-7",
     "book-of-mormon-episode-38-3-nephi-1-7-part-1",
     "book-of-mormon-episode-38-3-nephi-1-7-part-2",
     "book-of-mormon-episode-38-3-nephi-1-7-favorites"),
    (39, "3 Nephi 8-11",
     "book-of-mormon-episode-39-3-nephi-8-11-part-1",
     "book-of-mormon-episode-39-3-nephi-8-11-part-2",
     "book-of-mormon-episode-39-3-nephi-8-11-favorites"),
    (40, "3 Nephi 12-16",
     "book-of-mormon-episode-40-3-nephi-12-16-part-1",
     "book-of-mormon-episode-40-3-nephi-12-16-part-2",
     "book-of-mormon-episode-40-3-nephi-12-16-favorites"),
    # Episodes 41-52
    (41, "3 Nephi 17-19",
     "book-of-mormon-episode-41-3-nephi-17-19-part-1",
     "book-of-mormon-episode-41-3-nephi-17-19-part-2",
     "book-of-mormon-episode-41-3-nephi-17-19-favorites"),
    (42, "3 Nephi 20-26",
     "book-of-mormon-episode-42-3-nephi-20-26-part-1",
     "book-of-mormon-episode-42-3-nephi-20-26-part-2",
     "book-of-mormon-episode-42-3-nephi-20-26-favorites"),
    (43, "3 Nephi 27 - 4 Nephi",
     "book-of-mormon-episode-43-3-nephi-27-4-nephi-part-1",
     "book-of-mormon-episode-43-3-nephi-27-4-nephi-part-2",
     "book-of-mormon-episode-43-3-nephi-27-4-nephi-favorites"),
    (44, "Mormon 1-6",
     "book-of-mormon-episode-44-mormon-1-6-part-1",
     "book-of-mormon-episode-44-mormon-1-6-part-2",
     "book-of-mormon-episode-44-mormon-1-6-favorites"),
    (45, "Mormon 7-9",
     "book-of-mormon-episode-45-mormon-7-9-part-1",
     "book-of-mormon-episode-45-mormon-7-9-part-2",
     "book-of-mormon-episode-45-mormon-7-9-favorites"),
    (46, "Ether 1-5",
     "book-of-mormon-episode-46-ether-1-5-part-1",
     "book-of-mormon-episode-46-ether-1-5-part-2",
     "book-of-mormon-episode-46-ether-1-5-favorites"),
    (47, "Ether 6-11",
     "book-of-mormon-episode-47-ether-6-11-part-1",
     "book-of-mormon-episode-47-ether-6-11-part-2",
     "book-of-mormon-episode-47-ether-6-11-favorites"),
    (48, "Ether 12-15",
     "book-of-mormon-episode-48-ether-12-15-part-1",
     "book-of-mormon-episode-48-ether-12-15-part-2",
     "book-of-mormon-episode-48-ether-12-15-favorites"),
    (49, "Moroni 1-6",
     "book-of-mormon-episode-49-moroni-1-6-part-1",
     "book-of-mormon-episode-49-moroni-1-6-part-2",
     "book-of-mormon-episode-49-moroni-1-6-favorites"),
    (50, "Moroni 7-9",
     "book-of-mormon-episode-50-moroni-7-9-part-1",
     "book-of-mormon-episode-50-moroni-7-9-part-2",
     "book-of-mormon-episode-50-moroni-7-9-favorites"),
    (51, "Moroni 10",
     "book-of-mormon-episode-51-moroni-10-part-1",
     "book-of-mormon-episode-51-moroni-10-part-2",
     "book-of-mormon-episode-51-moroni-10-favorites"),
    (52, "Christmas",
     "book-of-mormon-episode-52-christmas-part-1",
     "book-of-mormon-episode-52-christmas-part-2",
     "3-24"),  # Favorites uses numeric slug
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/book-of-mormon-2024"):
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
        guest_pattern = re.compile(r'(?:Dr\.|Brother|Sister|Elder|President|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+')

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
        logging.info("Starting Follow Him Book of Mormon 2024 scraping...")
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
