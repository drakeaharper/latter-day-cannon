#!/usr/bin/env python3
"""
Follow Him Podcast Scraper - Doctrine and Covenants 2021

Scrapes all show notes (Part 1, Part 2, and Favorites) from the Follow Him podcast
for the 2021 Doctrine and Covenants year and saves them as markdown files.
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
        logging.FileHandler('followhim_dc2021_scraping.log'),
        logging.StreamHandler()
    ]
)

# Episode data: (episode_number, topic, part1_slug, part2_slug, favorites_slug)
# Note: D&C 2021 was the first season, so URL patterns are less consistent
EPISODES = [
    # Episodes 1-10 (mixed patterns, some episodes lack all three parts)
    (1, "Joseph Smith History; D&C 1", "2-240", "3-14", "3-15"),
    (2, "Joseph Smith History 1:1-26", "2-242", "2-241", "3-16"),
    (3, "Joseph Smith History 1:27-65", "2-244", "2-243", "3-19"),
    (4, "D&C 3-5", "2-246", "2-245", "3-20"),
    (5, "D&C 6-9", "2-247", "3-21", "3-22"),
    (6, "D&C 10-11", "2-248", "3-12", "3-23"),
    (7, "D&C 12-13; Joseph Smith History 1:66-75", "2-249", "3-13", "3-24"),
    (8, "D&C 14-17", "2-251", "2-250", "2-256"),
    (9, "D&C 18-19", "2-253", "2-252", "2-257"),
    (10, "D&C 20-22", "2-255", "2-254", "2-258"),
    # Episodes 11-20 (text-based slugs)
    (11, "D&C 23-26", "2-259", "2-260", "2-261"),
    (12, "D&C 27-28", "2-262", "2-263", "2-264"),
    (13, "D&C 29", "2-265", "2-266", "2-267"),
    (14, "Easter", "2-268", "2-269", "2-270"),
    (15, "D&C 30-36", "2-271", "2-272", "2-273"),
    (16, "D&C 37-40", "2-274", "2-275", "3-27"),
    (17, "D&C 41-44", "17-Doctrine-Covenants-41-44-Barbara-Gardner-followHIM-Podcast-show-notes-and-transcripts", "17-Doctrine-Covenants-41-44-Barbara-Gardner-followHIM-Podcast-show-notes-and-transcripts-2", "17-Doctrine-Covenants-41-44-Barbara-Gardner-followHIM-Podcast-Favorites"),
    (18, "D&C 45", "18-Doctrine-Covenants-45-Brent-L-Top-followHIM-show-notes-and-transcripts", "18-Doctrine-Covenants-45-Brent-L-Top-followHIM-show-notes-and-transcripts-2", "18-Doctrine-Covenants-45-Brent-L-Top-followHIM-Favorites"),
    (19, "D&C 46-48", "19-Doctrine-Covenants-46-48-Ron-Bartholomew-followHIM-Podcast-show-notes-and-transcripts", "19-Doctrine-Covenants-46-48-Ron-Bartholomew-followHIM-Podcast-show-notes-and-transcripts-2", "19-Doctrine-Covenants-46-48-Ron-Bartholomew-followHIM-Podcast-Favorites"),
    (20, "D&C 49-50", "20-Doctrine-Covenants-49-50-Lili-Anderson-followHIM-Podcast-show-notes-and-transcripts-merged", "20-Doctrine-Covenants-49-50-Lili-Anderson-followHIM-Podcast-show-notes-and-transcripts-2", "20-Doctrine-Covenants-49-50-Lili-Anderson-followHIM-Podcast-Favorites"),
    # Episodes 21-30 (numeric slugs)
    (21, "D&C 51-57", "2-278", "2-277", "2-276"),
    (22, "D&C 58-59", "2-281", "2-280", "2-279"),
    (23, "D&C 60-62", "2-284", "2-283", "2-282"),
    (24, "D&C 63", "2-287", "2-286", "2-285"),
    (25, "D&C 64-66", "2-290", "2-289", "2-288"),
    (26, "D&C 67-70", "2-293", "2-292", "2-291"),
    (27, "D&C 71-75", "2-296", "2-295", "2-294"),
    (28, "D&C 76", "2-299", "2-298", "2-297"),
    (29, "D&C 77-80", "2-302", "2-301", "2-300"),
    (30, "D&C 81-83", "2-305", "2-304", "2-303"),
    # Episodes 31-40 (numeric slugs, some estimated)
    (31, "D&C 84", "2-308", "2-307", "2-306"),
    (32, "D&C 85-87", "2-311", "2-310", "2-309"),
    (33, "D&C 88", "2-314", "2-313", "2-312"),
    (34, "D&C 89-92", "2-317", "2-316", "2-315"),
    (35, "D&C 93", "2-320", "2-319", "2-318"),
    (36, "D&C 94-97", "2-323", "2-322", "2-321"),
    (37, "D&C 98-101", "2-326", "2-325", "2-324"),
    (38, "D&C 102-105", "2-327", "2-328", "2-329"),
    (39, "D&C 106-108", "2-331", "2-330", "2-332"),
    (40, "D&C 109-110", "2-334", "2-333", "2-335"),
    # Episodes 41-52 (numeric slugs)
    (41, "D&C 111-114", "2-337", "2-336", "2-338"),
    (42, "D&C 115-120", "2-340", "2-339", "2-341"),
    (43, "D&C 121-123", "2-343", "2-342", "2-344"),
    (44, "D&C 124", "2-346", "2-345", "2-347"),
    (45, "D&C 125-128", "2-349", "2-348", "2-350"),
    (46, "D&C 129-132", "2-352", "2-351", "2-353"),
    (47, "D&C 133-134", "2-356", "2-355", "2-354"),
    (48, "D&C 135-136", "2-360", "2-359", "2-357"),
    (49, "D&C 136-137", "2-363", "2-361", "2-362"),
    (50, "Articles of Faith; Official Declarations", "2-365", "2-364", "2-366"),
    (51, "The Family Proclamation", "2-367", "2-368", "3-18"),
    (52, "Christmas", "2-370", "2-369", "2-371"),
]


class FollowHimScraper:
    """Scraper for Follow Him podcast show notes"""

    BASE_URL = "https://followhim.co"

    def __init__(self, output_dir="followhim/doctrine-and-covenants-2021"):
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
        logging.info("Starting Follow Him Doctrine and Covenants 2021 scraping...")
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
