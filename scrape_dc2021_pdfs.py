#!/usr/bin/env python3
"""
Download and parse PDF show notes for D&C 2021 Episodes 17-20
"""

import requests
from pathlib import Path
import re

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

# PDF URLs for missing episodes
EPISODES = [
    (17, "D&C 41-44", "Dr. Barbara Gardner",
     "https://followhim.co/wp-content/uploads/2025/04/17-Doctrine-Covenants-41-44-Barbara-Gardner-followHIM-Podcast-show-notes-and-transcripts.pdf"),
    (18, "D&C 45", "Dr. Brent L. Top",
     "https://followhim.co/wp-content/uploads/2025/04/18-Doctrine-Covenants-45-Brent-L-Top-followHIM-show-notes-and-transcripts.pdf"),
    (19, "D&C 46-48", "Dr. Ronald E. Bartholomew",
     "https://followhim.co/wp-content/uploads/2025/04/19-Doctrine-Covenants-46-48-Ron-Bartholomew-followHIM-Podcast-show-notes-and-transcripts.pdf"),
    (20, "D&C 49-50", "Dr. Lili De Hoyos Anderson",
     "https://followhim.co/wp-content/uploads/2025/05/20-Doctrine-Covenants-49-50-Lili-Anderson-followHIM-Podcast-show-notes-and-transcripts-merged.pdf"),
]

OUTPUT_DIR = Path("followhim/doctrine-and-covenants-2021")


def download_pdf(url, filepath):
    """Download PDF file"""
    print(f"Downloading: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        f.write(response.content)
    print(f"Saved to: {filepath}")
    return filepath


def extract_text_from_pdf(filepath):
    """Extract all text from PDF"""
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def split_into_parts(text, episode_num):
    """
    Try to split transcript into Part 1, Part 2, and Favorites
    based on common patterns in the transcripts
    """
    # Common patterns that might indicate part boundaries
    part1_markers = [
        r'Part\s*1',
        r'PART\s*ONE',
        r'Part\s*One',
    ]

    part2_markers = [
        r'Part\s*2',
        r'PART\s*TWO',
        r'Part\s*Two',
    ]

    favorites_markers = [
        r'Favorites',
        r'FAVORITES',
        r'followHIM\s+Favorites',
    ]

    # Try to find part boundaries
    part1_text = text
    part2_text = ""
    favorites_text = ""

    # Look for Part 2 marker
    for marker in part2_markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            split_pos = match.start()
            part1_text = text[:split_pos].strip()
            remaining = text[split_pos:].strip()

            # Look for Favorites marker in remaining text
            for fav_marker in favorites_markers:
                fav_match = re.search(fav_marker, remaining, re.IGNORECASE)
                if fav_match:
                    fav_pos = fav_match.start()
                    part2_text = remaining[:fav_pos].strip()
                    favorites_text = remaining[fav_pos:].strip()
                    break
            else:
                part2_text = remaining
            break

    # If no clear split, just use the whole text as Part 1
    if not part2_text:
        # Try splitting roughly by thirds if text is long enough
        lines = text.split('\n')
        if len(lines) > 100:
            third = len(lines) // 3
            part1_text = '\n'.join(lines[:third])
            part2_text = '\n'.join(lines[third:2*third])
            favorites_text = '\n'.join(lines[2*third:])
        else:
            part1_text = text
            part2_text = text  # Use same content if can't split
            favorites_text = ""

    return part1_text, part2_text, favorites_text


def clean_text(text):
    """Clean extracted PDF text"""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Fix common PDF extraction issues
    text = text.replace('\x00', '')
    return text.strip()


def save_markdown(episode_num, topic, guest, part_type, content, url):
    """Save content as markdown file"""
    safe_topic = re.sub(r'[<>:"/\\|?*;]', '', topic)
    filename = f"[Episode {episode_num:02d}][{safe_topic}][{part_type}].md"
    filepath = OUTPUT_DIR / filename

    md_content = f"Episode: {episode_num}\n"
    md_content += f"Topic: {topic}\n"
    md_content += f"Part: {part_type}\n"
    md_content += f"Guest: {guest}\n"
    md_content += f"URL: {url}\n\n"
    md_content += "---\n\n"
    md_content += f"# Episode {episode_num}: {topic} - {part_type}\n\n"
    md_content += content
    md_content += "\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"Saved: {filename}")
    return filepath


def process_episode(episode_num, topic, guest, pdf_url):
    """Download PDF and create markdown files for an episode"""
    print(f"\n{'='*50}")
    print(f"Processing Episode {episode_num}: {topic}")
    print(f"{'='*50}")

    # Download PDF to temp location
    temp_pdf = Path(f"/tmp/episode_{episode_num}.pdf")
    download_pdf(pdf_url, temp_pdf)

    # Extract text
    text = extract_text_from_pdf(temp_pdf)
    text = clean_text(text)

    print(f"Extracted {len(text)} characters from PDF")

    # Split into parts
    part1, part2, favorites = split_into_parts(text, episode_num)

    # Save markdown files
    save_markdown(episode_num, topic, guest, "Part 1", part1, pdf_url)
    save_markdown(episode_num, topic, guest, "Part 2", part2, pdf_url)
    if favorites:
        save_markdown(episode_num, topic, guest, "Favorites", favorites, pdf_url)
    else:
        # Create a minimal favorites file
        save_markdown(episode_num, topic, guest, "Favorites",
                     f"Favorites segment for Episode {episode_num}: {topic}\n\nSee Part 1 and Part 2 for full transcript.",
                     pdf_url)

    # Clean up temp file
    temp_pdf.unlink()

    print(f"Episode {episode_num} complete!")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for episode_num, topic, guest, pdf_url in EPISODES:
        try:
            process_episode(episode_num, topic, guest, pdf_url)
        except Exception as e:
            print(f"Error processing episode {episode_num}: {e}")

    print("\n" + "="*50)
    print("All episodes processed!")
    print("="*50)


if __name__ == "__main__":
    main()
