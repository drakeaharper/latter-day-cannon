#!/usr/bin/env python3
"""
Follow Him Podcast Scraper - New Testament 2023

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2023 New Testament year and saves them as markdown files.
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
        logging.FileHandler('followhim_nt2023_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_slug, part2_slug, favorites_slug)
EPISODES = [
    # Episodes 1-10
    (1, "We Are Responsible For Our Own Learning",
     "new-testament-episode-01-we-are-responsible-for-our-own-learning-part-1",
     "new-testament-episode-01-we-are-responsible-for-our-own-learning-part-2",
     "new-testament-episode-01-we-are-responsible-for-our-own-learning-favorites"),
    (2, "Matthew 1; Luke 1",
     "new-testament-episode-02-matthew-1-luke-1-part-1",
     "new-testament-episode-02-matthew-1-luke-1-part-2",
     "new-testament-episode-02-matthew-1-luke-1-favorites"),
    (3, "Matthew 2; Luke 2",
     "new-testament-episode-03-matthew-2-luke-2-part-1",
     "new-testament-episode-03-matthew-2-luke-2-part-2",
     "new-testament-episode-03-matthew-2-luke-2-favorites"),
    (4, "John 1",
     "new-testament-episode-04-john-1-part-1",
     "new-testament-episode-04-john-1-part-2",
     "new-testament-episode-04-john-1-favorites"),
    (5, "Matthew 3; Mark 1; Luke 3",
     "new-testament-episode-05-matthew-3-mark-1-luke-3-part-1",
     "new-testament-episode-05-matthew-3-mark-1-luke-3-part-2",
     "new-testament-episode-05-matthew-3-mark-1-luke-3-favorites"),
    (6, "Matthew 4; Luke 4-5",
     "new-testament-episode-06-matthew-4-luke-4-5-part-1",
     "new-testament-episode-06-matthew-4-luke-4-5-part-2",
     "new-testament-episode-06-matthew-4-luke-4-5-favorites"),
    (7, "John 2-4",
     "new-testament-episode-07-john-2-4-part-1",
     "new-testament-episode-07-john-2-4-part-2",
     "new-testament-episode-07-john-2-4-favorites"),
    (8, "Matthew 5; Luke 6",
     "new-testament-episode-08-matthew-5-luke-6-part-1",
     "new-testament-episode-08-matthew-5-luke-6-part-2",
     "new-testament-episode-08-matthew-5-luke-6-favorites"),
    (9, "Matthew 6-7",
     "new-testament-episode-09-matthew-6-7-part-1",
     "new-testament-episode-09-matthew-6-7-part-2",
     "new-testament-episode-09-matthew-6-7-favorites"),
    (10, "Matthew 8; Mark 2-4; Luke 7",
     "new-testament-episode-10-matthew-8-mark-2-4-luke-7-part-1",
     "new-testament-episode-10-matthew-8-mark-2-4-luke-7-part-2",
     "new-testament-episode-10-matthew-8-mark-2-4-luke-7-favorites"),
    # Episodes 11-20
    (11, "Matthew 9-10; Mark 5; Luke 9",
     "new-testament-episode-11-matthew-9-10-mark-5-luke-9-part-1",
     "new-testament-episode-11-matthew-9-10-mark-5-luke-9-part-2",
     "new-testament-episode-11-matthew-9-10-mark-5-luke-9-favorites"),
    (12, "Matthew 11-12; Luke 11",
     "new-testament-episode-12-matthew-11-12-luke-11-part-1",
     "new-testament-episode-12-matthew-11-12-luke-11-part-2",
     "new-testament-episode-19-luke-12-17-john-11-favorites"),  # Note: Different favorites slug
    (13, "Matthew 13; Luke 8-13",
     "new-testament-episode-13-matthew-13-luke-8-13-part-1",
     "new-testament-episode-13-matthew-13-luke-8-13-part-2",
     "new-testament-episode-13-matthew-13-luke-8-13-favorites"),
    (14, "Matthew 14; Mark 6; John 5-6",
     "new-testament-episode-14-matthew-14-mark-6-john-5-6-part-1",
     "new-testament-episode-14-matthew-14-mark-6-john-5-6-part-2",
     "new-testament-episode-14-matthew-14-mark-6-john-5-6-favorites"),
    (15, "Easter",
     "new-testament-episode-15-easter-part-1",
     "new-testament-episode-15-easter-part-2",
     "new-testament-episode-16-matthew-15-17-mark-7-9-favorites"),  # Note: Different favorites slug
    (16, "Matthew 15-17; Mark 7-9",
     "new-testament-episode-16-matthew-15-17-mark-7-9-part-1",
     "new-testament-episode-16-matthew-15-17-mark-7-9-part-2",
     "new-testament-episode-16-matthew-15-17-mark-7-9-favorites"),
    (17, "Matthew 18; Luke 10",
     "new-testament-episode-17-matthew-18-luke-10-part-1",
     "new-testament-episode-17-matthew-18-luke-10-part-2",
     "new-testament-episode-17-matthew-18-luke-10-favorites"),
    (18, "John 7-10",
     "new-testament-episode-18-john-7-10-part-1",
     "new-testament-episode-18-john-7-10-part-2",
     "new-testament-episode-18-john-7-10-favorites"),
    (19, "Luke 12-17; John 11",
     "new-testament-episode-19-luke-12-17-john-11-part-1",
     "new-testament-episode-19-luke-12-17-john-11-part-2",
     "new-testament-episode-19-luke-12-17-john-11-favorites"),
    (20, "Matthew 19-20; Mark 10; Luke 18",
     "new-testament-episode-20-matthew-19-20-mark-10-luke-18-part-1",
     "new-testament-episode-20-matthew-19-20-mark-10-luke-18-part-2",
     "new-testament-episode-20-matthew-19-20-mark-10-luke-18-favorites"),
    # Episodes 21-30 (use numeric slugs)
    (21, "Matthew 21-23; Mark 11; Luke 19-20; John 12",
     "2-524", "2-9", "3"),
    (22, "Joseph Smith-Matthew 1; Matthew 24-25; Mark 12-13; Luke 21",
     "7-2", "2-8", "2"),
    (23, "Matthew 26; Mark 14; John 13",
     "2-7", "2-6", "3-2"),
    (24, "John 14-17",
     "2-5", "3-3", "2-2"),
    (25, "Luke 22; John 18",
     "7", "2-4", "2-3"),
    (26, "Matthew 27; Mark 15; Luke 23; John 19",
     "3-6", "3-5", "3-4"),
    (27, "Matthew 28; Mark 16; Luke 24; John 20-21",
     "2-12", "2-11", "2-10"),
    (28, "Acts 1-5",
     "2-14", "3-7", "2-13"),
    (29, "Acts 6-9",
     "2-17", "2-16", "2-15"),
    (30, "Acts 10-15",
     "2-20", "2-19", "2-18"),
    # Episodes 31-40
    (31, "Acts 16-21",
     "2-23", "2-22", "2-21"),
    (32, "Acts 22-28",
     "2-26", "2-25", "2-24"),
    (33, "Romans 1-6",
     "2-29", "2-28", "2-27"),
    (34, "Romans 7-16",
     "2-32", "2-31", "2-30"),
    (35, "1 Corinthians 1-7",
     "2-35", "2-34", "2-33"),
    (36, "1 Corinthians 8-13",
     "2-38", "2-37", "2-36"),
    (37, "1 Corinthians 14-16",
     "2-41", "2-40", "2-39"),
    (38, "2 Corinthians 1-7",
     "2-44", "2-43", "2-42"),
    (39, "2 Corinthians 8-13",
     "2-47", "2-46", "2-45"),
    (40, "Galatians",
     "2-50", "2-49", "2-48"),
    # Episodes 41-53
    (41, "Ephesians",
     "2-53", "2-52", "2-51"),
    (42, "Philippians; Colossians",
     "2-56", "2-55", "2-54"),
    (43, "1 & 2 Thessalonians",
     "2-59", "2-58", "2-57"),
    (44, "1 & 2 Timothy; Titus; Philemon",
     "2-62", "2-61", "2-60"),
    (45, "Hebrews 1-6",
     "2-65", "2-64", "2-63"),
    (46, "Hebrews 7-13",
     "2-68", "2-67", "2-66"),
    (47, "James",
     "2-71", "2-70", "2-69"),
    (48, "1 & 2 Peter",
     "2-74", "2-73", "2-72"),
    (49, "1-3 John; Jude",
     "2-77", "2-76", "2-75"),
    (50, "Revelation 1-5",
     "2-80", "2-79", "2-78"),
    (51, "Revelation 6-14",
     "2-83", "2-82", "2-81"),
    (52, "Christmas",
     "2-86", "2-85", "2-84"),
    (53, "Revelation 15-22",
     "2-89", "2-88", "2-87"),
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/new-testament-2023"):
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
        logging.info("Starting Follow Him New Testament 2023 scraping...")
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
