#!/usr/bin/env python3
"""
General Conference Scraper for LDS General Conference Talks

Scrapes all talks from LDS General Conferences and saves them as markdown files.
Each talk includes speaker, title, session, and full talk content.
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
        logging.FileHandler('general_conference_scraping.log'),
        logging.StreamHandler()
    ]
)

class GeneralConferenceScraper:
    """Scraper for LDS General Conference Talks"""

    BASE_URL = "https://www.churchofjesuschrist.org"
    INDEX_URL = f"{BASE_URL}/study/general-conference?lang=eng"

    def __init__(self, output_dir="general_conference"):
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

    def discover_conferences(self):
        """Discover all conferences from the index page"""
        logging.info("Discovering conferences from index page...")
        html = self.fetch_page(self.INDEX_URL)
        if not html:
            logging.error("Failed to fetch index page")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        conferences = []

        # Find all links to individual conference pages
        # Pattern: /study/general-conference/YYYY/MM?lang=eng
        links = soup.find_all('a', href=re.compile(r'/study/general-conference/\d{4}/(04|10)(\?lang=eng)?'))

        for link in links:
            href = link.get('href')
            # Remove query parameters for comparison
            clean_href = href.split('?')[0]

            # Extract year and month from URL
            match = re.search(r'/general-conference/(\d{4})/(04|10)', clean_href)
            if match:
                year = match.group(1)
                month = match.group(2)
                full_url = self.BASE_URL + clean_href + "?lang=eng"
                conferences.append((year, month, full_url))

        # Remove duplicates while preserving order
        seen = set()
        unique_conferences = []
        for year, month, url in conferences:
            key = (year, month)
            if key not in seen:
                seen.add(key)
                unique_conferences.append((year, month, url))

        # Sort by year and month (most recent first)
        unique_conferences.sort(key=lambda x: (x[0], x[1]), reverse=True)

        logging.info(f"Discovered {len(unique_conferences)} unique conferences")
        return unique_conferences

    def is_talk_url(self, href):
        """Determine if a URL is a talk (not a session)"""
        # Talk URLs have numeric prefix + speaker name: /2025/10/12stevenson
        # Session URLs have descriptive names: /2025/10/saturday-morning-session
        if not href:
            return False

        # Extract the last part of the URL
        parts = href.rstrip('/').split('/')
        if len(parts) < 2:
            return False

        last_part = parts[-1].split('?')[0]  # Remove query params

        # Check if it starts with a digit (talk URLs do, session URLs don't)
        return bool(re.match(r'^\d+', last_part))

    def discover_talks(self, conference_url):
        """Discover all talks from a conference page"""
        logging.info(f"Discovering talks from: {conference_url}")
        html = self.fetch_page(conference_url)
        if not html:
            logging.error(f"Failed to fetch conference page: {conference_url}")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        talks = []

        # Find all links within the conference page
        links = soup.find_all('a', href=re.compile(r'/study/general-conference/\d{4}/(04|10)/'))

        for link in links:
            href = link.get('href')

            # Only include talk URLs (not session URLs)
            if self.is_talk_url(href):
                talk_title = link.get_text(strip=True)
                if talk_title:
                    full_url = self.BASE_URL + href if href.startswith('/') else href
                    talks.append((talk_title, full_url))

        # Remove duplicates while preserving order
        seen = set()
        unique_talks = []
        for title, url in talks:
            if url not in seen:
                seen.add(url)
                unique_talks.append((title, url))

        logging.info(f"Discovered {len(unique_talks)} talks")
        return unique_talks

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def extract_talk_content(self, url):
        """Extract content from a talk page"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata from URL
        # Pattern: /study/general-conference/YYYY/MM/##speakername
        url_match = re.search(r'/general-conference/(\d{4})/(04|10)/(\d+)([a-z-]+)', url)
        if url_match:
            year = url_match.group(1)
            month = "October" if url_match.group(2) == "10" else "April"
            talk_id = url_match.group(3)
            speaker_slug = url_match.group(4)
        else:
            logging.warning(f"Could not parse URL: {url}")
            return None

        # Extract talk title
        title_elem = soup.find('h1')
        talk_title = self.clean_text(title_elem.get_text()) if title_elem else "Unknown Title"

        # Extract speaker name and calling
        speaker_name = "Unknown Speaker"
        speaker_calling = ""

        # Look for author byline
        author_elem = soup.find('p', class_='author-name')
        if author_elem:
            speaker_name = self.clean_text(author_elem.get_text())

        # Look for role/calling
        role_elem = soup.find('p', class_='author-role')
        if role_elem:
            speaker_calling = self.clean_text(role_elem.get_text())

        # Extract session information
        session = ""
        # Try to find session in metadata or breadcrumbs
        kicker_elem = soup.find('p', class_='kicker')
        if kicker_elem:
            session_text = self.clean_text(kicker_elem.get_text())
            # Extract session name if present
            if 'Session' in session_text:
                session = session_text

        # If not found, try to infer from URL or page structure
        if not session:
            # Look for session link in navigation
            nav_links = soup.find_all('a', href=re.compile(r'(morning|afternoon|evening)-session'))
            if nav_links:
                session = self.clean_text(nav_links[0].get_text())

        # Extract main body content
        body = soup.find('div', class_='body-block')
        if not body:
            logging.warning(f"No body content found for {url}")
            return None

        # Extract paragraphs and headings
        content_parts = []

        for elem in body.find_all(['p', 'h2', 'h3', 'blockquote']):
            if elem.name in ['h2', 'h3']:
                # Headings
                heading_text = self.clean_text(elem.get_text())
                if heading_text:
                    content_parts.append(f"\n## {heading_text}\n")
            elif elem.name == 'blockquote':
                # Block quotes
                quote_text = self.clean_text(elem.get_text())
                if quote_text:
                    content_parts.append(f"\n> {quote_text}\n")
            else:
                # Paragraphs
                # Remove footnote references but keep the text
                for sup in elem.find_all('sup', class_='marker'):
                    sup.decompose()

                para_text = self.clean_text(elem.get_text())
                if para_text:
                    content_parts.append(para_text + "\n")

        content = '\n'.join(content_parts)

        return {
            'year': year,
            'month': month,
            'talk_id': talk_id,
            'speaker_slug': speaker_slug,
            'title': talk_title,
            'speaker_name': speaker_name,
            'speaker_calling': speaker_calling,
            'session': session,
            'url': url,
            'content': content.strip()
        }

    def save_talk(self, talk_data):
        """Save talk data as markdown file"""
        if not talk_data:
            return

        # Create directory structure: general_conference/YYYY/MM/
        year_dir = self.output_dir / talk_data['year']
        month_dir = year_dir / talk_data['month'].lower()
        month_dir.mkdir(parents=True, exist_ok=True)

        # Create filename: [YYYY-MM][##speakername][Talk Title].md
        month_num = "10" if talk_data['month'] == "October" else "04"
        filename = f"[{talk_data['year']}-{month_num}][{talk_data['talk_id']}{talk_data['speaker_slug']}][{talk_data['title']}].md"

        # Clean filename of invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filepath = month_dir / filename

        # Build markdown content
        content = f"Year: {talk_data['year']}\n"
        content += f"Month: {talk_data['month']}\n"
        content += f"Speaker: {talk_data['speaker_name']}\n"
        if talk_data['speaker_calling']:
            content += f"Calling: {talk_data['speaker_calling']}\n"
        content += f"Title: {talk_data['title']}\n"
        if talk_data['session']:
            content += f"Session: {talk_data['session']}\n"
        content += f"URL: {talk_data['url']}\n\n"
        content += "---\n\n"
        content += talk_data['content']

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved: {filename}")
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")

    def scrape_all(self, start_year=None, end_year=None):
        """Scrape all conferences"""
        logging.info("Starting General Conference scraping...")

        # Discover all conferences
        conferences = self.discover_conferences()
        if not conferences:
            logging.error("No conferences discovered")
            return

        # Filter by year range if specified
        if start_year or end_year:
            filtered = []
            for year, month, url in conferences:
                year_int = int(year)
                if start_year and year_int < start_year:
                    continue
                if end_year and year_int > end_year:
                    continue
                filtered.append((year, month, url))
            conferences = filtered

        logging.info(f"Found {len(conferences)} conferences to scrape")

        # Scrape each conference
        total_talks = 0
        successful = 0
        failed = 0

        for i, (year, month, conference_url) in enumerate(conferences, 1):
            month_name = "October" if month == "10" else "April"
            logging.info(f"\n[{i}/{len(conferences)}] Processing: {month_name} {year}")

            # Discover talks in this conference
            talks = self.discover_talks(conference_url)
            total_talks += len(talks)

            # Scrape each talk
            for j, (talk_title, talk_url) in enumerate(talks, 1):
                logging.info(f"  [{j}/{len(talks)}] Processing talk: {talk_title}")

                try:
                    talk_data = self.extract_talk_content(talk_url)
                    if talk_data:
                        self.save_talk(talk_data)
                        successful += 1
                    else:
                        logging.warning(f"Failed to extract content for: {talk_title}")
                        failed += 1
                except Exception as e:
                    logging.error(f"Error processing {talk_title}: {e}")
                    failed += 1

                # Rate limiting
                time.sleep(2)

            # Delay between conferences
            time.sleep(3)

        logging.info(f"\n{'='*60}")
        logging.info(f"Scraping complete!")
        logging.info(f"Conferences processed: {len(conferences)}")
        logging.info(f"Total talks: {total_talks}")
        logging.info(f"Successful: {successful}")
        logging.info(f"Failed: {failed}")
        logging.info(f"{'='*60}")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Scrape LDS General Conference talks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Scrape a specific conference
  python3 scrape_general_conference.py --year 2025 --month 10

  # Scrape all conferences from a specific year
  python3 scrape_general_conference.py --year 2025

  # Scrape a range of years
  python3 scrape_general_conference.py --start-year 2023 --end-year 2025

  # Scrape all available conferences
  python3 scrape_general_conference.py --all
        '''
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true',
                      help='Scrape all available conferences')
    group.add_argument('--year', type=int,
                      help='Scrape a specific year (e.g., 2025)')
    group.add_argument('--start-year', type=int,
                      help='Start year for range scraping')

    parser.add_argument('--month', type=int, choices=[4, 10],
                       help='Specific month (4=April, 10=October), requires --year')
    parser.add_argument('--end-year', type=int,
                       help='End year for range scraping, requires --start-year')

    args = parser.parse_args()

    scraper = GeneralConferenceScraper()

    # Validate arguments
    if args.month and not args.year:
        parser.error('--month requires --year')
    if args.end_year and not args.start_year:
        parser.error('--end-year requires --start-year')

    # Handle different scraping modes
    if args.all:
        print("Scraping all available conferences...")
        scraper.scrape_all()

    elif args.year:
        if args.month:
            print(f"Scraping {['', '', '', '', 'April', '', '', '', '', '', 'October'][args.month]} {args.year}...")
            month_name = "10" if args.month == 10 else "04"
            conference_url = f"{scraper.BASE_URL}/study/general-conference/{args.year}/{month_name}?lang=eng"

            # Scrape single conference
            talks = scraper.discover_talks(conference_url)
            successful = 0
            failed = 0

            for j, (talk_title, talk_url) in enumerate(talks, 1):
                print(f"  [{j}/{len(talks)}] Processing: {talk_title}")
                try:
                    talk_data = scraper.extract_talk_content(talk_url)
                    if talk_data:
                        scraper.save_talk(talk_data)
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logging.error(f"Error processing {talk_title}: {e}")
                    failed += 1
                time.sleep(2)

            print(f"\nComplete! Successful: {successful}, Failed: {failed}")

        else:
            print(f"Scraping all conferences from {args.year}...")
            scraper.scrape_all(start_year=args.year, end_year=args.year)

    elif args.start_year:
        end = args.end_year if args.end_year else args.start_year
        print(f"Scraping conferences from {args.start_year} to {end}...")
        scraper.scrape_all(start_year=args.start_year, end_year=end)

if __name__ == "__main__":
    main()
