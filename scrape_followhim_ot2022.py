#!/usr/bin/env python3
"""
Follow Him Podcast Scraper - Old Testament 2022

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2022 Old Testament year and saves them as markdown files.
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
        logging.FileHandler('followhim_ot2022_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_slug, part2_slug, favorites_slug)
EPISODES = [
    # Episodes 1-10
    (1, "Moses 1; Abraham 3", "2-91", "2-90", "2-89"),
    (2, "Genesis 1-3; Moses 2-3; Abraham 4-5", "2-93", "2-92", "3-7"),
    (3, "Genesis 3-4; Moses 4-5", "2-95", "2-94", "3-8"),
    (4, "Genesis 5; Moses 6", "2-98", "2-97", "2-96"),
    (5, "Moses 7", "2-101", "2-100", "2-99"),
    (6, "Genesis 6-11; Moses 8", "2-104", "2-103", "2-102"),
    (7, "Genesis 12-17; Abraham 1-2", "2-107", "2-106", "2-105"),
    (8, "Genesis 18-23", "2-110", "2-109", "2-108"),
    (9, "Genesis 24-27", "2-113", "2-112", "2-111"),
    (10, "Genesis 28-33", "2-116", "2-115", "2-114"),
    # Episodes 11-20
    (11, "Genesis 37-41", "2-119", "2-118", "2-117"),
    (12, "Genesis 42-50", "2-122", "2-121", "2-120"),
    (13, "Exodus 1-6", "2-125", "2-124", "2-123"),
    (14, "Exodus 7-13", "2-128", "2-127", "2-126"),
    (15, "Exodus 14-17", "2-131", "2-130", "2-129"),
    (16, "Easter", "2-134", "2-133", "2-132"),
    (17, "Exodus 18-20", "2-137", "2-136", "2-135"),
    (18, "Exodus 24; 31-34", "2-140", "2-139", "2-138"),
    (19, "Exodus 35-40; Leviticus 1; 16; 19", "2-143", "2-142", "2-141"),
    (20, "Numbers 11-14; 20-24", "2-146", "2-145", "2-144"),
    # Episodes 21-30
    (21, "Deuteronomy 6-8; 15; 18; 29-30; 34", "2-149", "2-148", "2-147"),
    (22, "Joshua 1-8; 23-24", "2-152", "2-151", "2-150"),
    (23, "Judges 2-4; 6-8; 13-16", "2-155", "2-154", "2-153"),
    (24, "Ruth; 1 Samuel 1-3", "2-158", "2-157", "2-156"),
    (25, "1 Samuel 8-10; 13; 15-18", "2-161", "2-160", "2-159"),
    (26, "2 Samuel 5-7; 11-12; 1 Kings 3; 8; 11", "2-164", "2-163", "2-162"),
    (27, "1 Kings 17-19", "2-167", "2-166", "2-165"),
    (28, "2 Kings 2-7", "2-170", "2-169", "2-168"),
    (29, "2 Kings 17-25", "2-173", "2-172", "2-171"),
    (30, "Ezra 1; 3-7; Nehemiah 2; 4-6; 8", "2-176", "2-175", "2-174"),
    # Episodes 31-40
    (31, "Esther", "2-179", "2-178", "2-177"),
    (32, "Job", "2-182", "2-181", "2-180"),
    (33, "Psalms 1-46", "2-185", "2-184", "2-183"),
    (34, "Psalms 49-51; 61-66; 69-72; 77-78; 85-86", "2-188", "2-187", "2-186"),
    (35, "Psalms 102-150", "2-191", "2-189", "2-190"),
    (36, "Proverbs 1-4; 15-16; 22; 31; Ecclesiastes 1-3; 11-12", "2-194", "2-193", "2-192"),
    (37, "Isaiah 1-12", "2-197", "2-196", "2-195"),
    (38, "Isaiah 13-35", "2-200", "2-199", "2-198"),
    (39, "Isaiah 40-49", "2-203", "2-202", "2-201"),
    (40, "Isaiah 50-57", "2-206", "2-205", "2-204"),
    # Episodes 41-52
    (41, "Isaiah 58-66", "2-208", "3-9", "2-207"),
    (42, "Jeremiah 1-29", "2-211", "2-210", "2-209"),
    (43, "Jeremiah 30-52; Lamentations", "2-214", "2-213", "2-212"),
    (44, "Ezekiel 1-3; 33-34; 36-37; 47", "2-217", "2-216", "2-215"),
    (45, "Daniel 1-6", "2-220", "2-219", "2-218"),
    (46, "Hosea 1-6; 10-14; Joel", "2-223", "2-222", "2-221"),
    (47, "Amos; Obadiah", "2-225", "2-224", "3-10"),
    (48, "Jonah; Micah", "2-228", "2-227", "2-226"),
    (49, "Nahum; Habakkuk; Zephaniah", "2-231", "2-230", "2-229"),
    (50, "Haggai; Zechariah 1-3; 7-14", "2-234", "3-11", "2-232"),
    (51, "Malachi", "2-236", "2-233", "2-235"),
    (52, "Christmas", "2-239", "2-238", "2-237"),
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/old-testament-2022"):
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
        logging.info("Starting Follow Him Old Testament 2022 scraping...")
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
