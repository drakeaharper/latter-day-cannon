#!/usr/bin/env python3
"""
Follow Him Podcast Scraper - Old Testament 2026

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2026 Old Testament year and saves them as markdown files.
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('followhim_ot2026_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_slug, part2_slug, favorites_slug)
EPISODES = [
    (1, "Introduction to the Old Testament", "3-31", "3-30", "3-29"),
    (2, "Moses 1; Abraham 3", "2-533", "2-532", "2-531"),
    (3, "Genesis 1-2; Moses 2-3; Abraham 4-5", "2-536", "2-535-2", "2-535"),
    (4, "Genesis 3-4; Moses 4-5", "2-539", "2-538", "2-537"),
    (5, "Genesis 5; Moses 6", "2-542", "2-541", "2-540"),
    (6, "Moses 7", "2-545", "2-543", "2-544"),
    (7, "Genesis 6-9; Moses 8", "2-548", "2-547", "2-546"),
    (8, "Genesis 12-17; Abraham 1-2", "old-testament-episode-8-2026-genesis-12-17-abraham-1-2-part-1", "old-testament-episode-8-2026-genesis-12-17-abraham-1-2-part-2", "old-testament-episode-8-2026-genesis-12-17-abraham-1-2-favorites"),
    (9, "Genesis 18-23", "old-testament-episode-9-2026-genesis-18-23-part-1", "old-testament-episode-9-2026-genesis-18-23-part-2", "old-testament-episode-9-2026-genesis-18-23-favorites"),
    (10, "Genesis 24-33", "old-testament-episode-10-2026-genesis-24-33-part-1", "old-testament-episode-10-2026-genesis-24-33-part-2", "old-testament-episode-10-2026-genesis-24-33-favorites"),
    (11, "Genesis 37-41", "old-testament-episode-11-2026-genesis-37-41-part-1", "old-testament-episode-11-2026-genesis-37-41-part-2", "old-testament-episode-11-2026-genesis-37-41-favorites"),
    (12, "Genesis 42-50", "old-testament-episode-12-2026-genesis-42-50-part-1", "old-testament-episode-12-2026-genesis-42-50-part-2", "old-testament-episode-12-2026-genesis-42-50-favorites"),
    (13, "Exodus 1-6", "old-testament-episode-13-2026-exodus-1-6-part-1", "old-testament-episode-13-2026-exodus-1-6-part-2", "old-testament-episode-13-2026-exodus-1-6-favorites"),
]

# Thoughts to Keep in Mind episodes: (number, topic, slug)
THOUGHTS_EPISODES = [
    (1, "Reading the Old Testament", "2-534"),
    (2, "The Covenant", "thoughts-to-keep-in-mind-episode-2-the-covenant"),
    (3, "The House of Israel", "thoughts-to-keep-in-mind-episode-3-the-house-of-israel"),
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/old-testament-2026"):
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
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text

    def extract_guest_from_transcript(self, transcript):
        """Extract guest name from transcript speaker attributions."""
        hosts = {'Hank Smith', 'John Bytheway'}

        # Pattern with titles
        speaker_pattern = re.compile(
            r'^((?:Dr\.|Pres\.|President|Sister|Sis\.|Brother|Bro\.|Elder|Bishop|Prof\.?)\s*'
            r'(?:[A-Z]\.?[A-Z]?\.?\s+)?'
            r'[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s*[A-Z]?[a-z]*):\s*\d{1,2}:\d{2}',
            re.MULTILINE
        )

        # Simple pattern without title
        simple_pattern = re.compile(
            r'^([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+):\s*\d{1,2}:\d{2}',
            re.MULTILINE
        )

        speakers = set()

        for match in speaker_pattern.finditer(transcript):
            speakers.add(match.group(1).strip())

        for match in simple_pattern.finditer(transcript):
            speakers.add(match.group(1).strip())

        # Normalize abbreviations
        normalized = set()
        for speaker in speakers:
            s = speaker
            s = re.sub(r'^Pres\.\s*', 'President ', s)
            s = re.sub(r'^Sis\.\s*', 'Sister ', s)
            s = re.sub(r'^Bro\.\s*', 'Brother ', s)
            s = re.sub(r'^Prof\.\s*', 'Professor ', s)
            normalized.add(s.strip())

        guests = normalized - hosts
        return sorted(guests)[0] if guests else None

    def extract_show_notes(self, url):
        """Extract content from a show notes page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find('title')
        title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown Title"

        content_area = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('main')

        if not content_area:
            content_area = soup.find('body')

        if not content_area:
            logging.warning(f"No content found for {url}")
            return None

        for script in content_area(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        paragraphs = content_area.find_all(['p', 'h2', 'h3', 'h4'])

        transcript_lines = []
        for elem in paragraphs:
            text = self.clean_text(elem.get_text())
            if text and len(text) > 10:
                transcript_lines.append(text)

        transcript = '\n\n'.join(transcript_lines)
        guest = self.extract_guest_from_transcript(transcript)
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

        safe_topic = re.sub(r'[<>:"/\\|?*;]', '', topic)
        filename = f"[Episode {episode_num:02d}][{safe_topic}][{part_type}].md"
        filepath = self.output_dir / filename

        content = f"Episode: {episode_num}\n"
        content += f"Topic: {topic}\n"
        content += f"Part: {part_type}\n"
        if data.get('guest'):
            content += f"Guest: {data['guest']}\n"
        content += f"URL: {data['url']}\n\n"
        content += "---\n\n"
        content += f"# {data['title']}\n\n"
        content += data['transcript']
        content += "\n"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")
            return False

    def save_thoughts_episode(self, episode_num, topic, data):
        """Save Thoughts to Keep in Mind episode as markdown file (in its own series directory)"""
        if not data:
            return False

        # Thoughts episodes go in their own directory like Voices of the Restoration
        thoughts_dir = Path("followhim/thoughts-to-keep-in-mind")
        thoughts_dir.mkdir(parents=True, exist_ok=True)

        safe_topic = re.sub(r'[<>:"/\\|?*;]', '', topic)
        filename = f"[Episode {episode_num:02d}][{safe_topic}].md"
        filepath = thoughts_dir / filename

        # Format like Voices of the Restoration
        content = f"Episode: {episode_num}\n"
        content += f"Series: Thoughts to Keep in Mind\n"
        content += f"Topic: {topic}\n"
        if data.get('guest'):
            content += f"Guest: {data['guest']}\n"
        content += f"URL: {data['url']}\n\n"
        content += "---\n\n"
        content += f"# {data['title']}\n\n"
        content += data['transcript']
        content += "\n"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename} (Thoughts to Keep in Mind)")
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

        logging.info(f"[Episode {episode_num}] Scraping Part 1...")
        url = self.build_url(part1_slug)
        data = self.extract_show_notes(url)
        if data:
            results['part1'] = self.save_show_notes(episode_num, topic, "Part 1", data)
        time.sleep(2)

        logging.info(f"[Episode {episode_num}] Scraping Part 2...")
        url = self.build_url(part2_slug)
        data = self.extract_show_notes(url)
        if data:
            results['part2'] = self.save_show_notes(episode_num, topic, "Part 2", data)
        time.sleep(2)

        logging.info(f"[Episode {episode_num}] Scraping Favorites...")
        url = self.build_url(favorites_slug)
        data = self.extract_show_notes(url)
        if data:
            results['favorites'] = self.save_show_notes(episode_num, topic, "Favorites", data)
        time.sleep(2)

        return results

    def scrape_thoughts_episode(self, episode_num, topic, slug):
        """Scrape a Thoughts to Keep in Mind episode"""
        logging.info(f"[Thoughts {episode_num}] Scraping {topic}...")
        url = self.build_url(slug)
        data = self.extract_show_notes(url)
        if data:
            return self.save_thoughts_episode(episode_num, topic, data)
        return False

    def scrape_all(self):
        """Scrape all episodes"""
        logging.info("Starting Follow Him Old Testament 2026 scraping...")
        logging.info(f"Regular episodes to scrape: {len(EPISODES)}")
        logging.info(f"Thoughts episodes to scrape: {len(THOUGHTS_EPISODES)}")

        successful = 0
        failed = 0

        # Scrape regular episodes
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

        # Scrape Thoughts to Keep in Mind episodes
        for thoughts_ep in THOUGHTS_EPISODES:
            ep_num, topic, slug = thoughts_ep
            logging.info(f"\nProcessing: Thoughts {ep_num} - {topic}")

            try:
                if self.scrape_thoughts_episode(ep_num, topic, slug):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Error processing Thoughts {ep_num}: {e}")
                failed += 1

        logging.info(f"\n{'='*50}")
        logging.info(f"Scraping complete!")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")


def main():
    scraper = FollowHimScraper()
    scraper.scrape_all()


if __name__ == "__main__":
    main()
