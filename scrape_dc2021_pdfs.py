#!/usr/bin/env python3
"""
Download and parse PDF show notes for D&C 2021 Episodes 17-20
Properly extracts transcript content and splits into Part 1 and Part 2
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
    return filepath


def extract_text_from_pdf(filepath):
    """Extract all text from PDF"""
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def find_transcript_start(text):
    """Find where the actual transcript begins (first 'Hank Smith:' line)"""
    match = re.search(r'Hank Smith:\s*\d{2}:\d{2}', text)
    if match:
        return match.start()
    # Fallback: look for just "Hank Smith:"
    match = re.search(r'Hank Smith:', text)
    if match:
        return match.start()
    return 0


def split_transcript(transcript):
    """
    Split transcript into Part 1 and Part 2
    Look for markers like "Welcome to part two" or "join us for part two"
    """
    # Find Part 2 boundary
    part2_patterns = [
        r'Welcome to [Pp]art [Tt]wo',
        r'Welcome to [Pp]art 2',
        r'Welcome to [Pp]art II',
        r'join us for [Pp]art [Tt]wo',
        r'join us for [Pp]art 2',
    ]

    part2_start = None
    for pattern in part2_patterns:
        match = re.search(pattern, transcript)
        if match:
            # Find the start of the line containing this match
            # Go back to find "Hank Smith:" before this
            search_start = max(0, match.start() - 500)
            pre_text = transcript[search_start:match.start()]
            hank_match = re.search(r'Hank Smith:\s*\d{2}:\d{2}[^\n]*$', pre_text)
            if hank_match:
                part2_start = search_start + hank_match.start()
            else:
                part2_start = match.start()
            break

    if part2_start and part2_start > 10000:  # Make sure Part 1 has substantial content
        part1 = transcript[:part2_start].strip()
        part2 = transcript[part2_start:].strip()
    else:
        # No clear split found - divide roughly in half
        midpoint = len(transcript) // 2
        # Try to find a good break point near the middle
        search_range = transcript[midpoint-5000:midpoint+5000]
        break_match = re.search(r'\n\s*\n', search_range)
        if break_match:
            actual_midpoint = midpoint - 5000 + break_match.end()
            part1 = transcript[:actual_midpoint].strip()
            part2 = transcript[actual_midpoint:].strip()
        else:
            part1 = transcript[:midpoint].strip()
            part2 = transcript[midpoint:].strip()

    return part1, part2


def extract_show_notes(text):
    """Extract show notes section (before transcript)"""
    transcript_start = find_transcript_start(text)
    if transcript_start > 0:
        return text[:transcript_start].strip()
    return ""


def clean_text(text):
    """Clean extracted PDF text"""
    # Remove excessive whitespace but preserve paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
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

    print(f"Saved: {filename} ({len(content):,} chars)")
    return filepath


def process_episode(episode_num, topic, guest, pdf_url):
    """Download PDF and create markdown files for an episode"""
    print(f"\n{'='*60}")
    print(f"Processing Episode {episode_num}: {topic}")
    print(f"{'='*60}")

    # Download PDF to temp location
    temp_pdf = Path(f"/tmp/episode_{episode_num}.pdf")
    download_pdf(pdf_url, temp_pdf)

    # Extract text
    full_text = extract_text_from_pdf(temp_pdf)
    full_text = clean_text(full_text)
    print(f"Extracted {len(full_text):,} characters from PDF")

    # Find transcript start
    transcript_start = find_transcript_start(full_text)
    print(f"Transcript starts at position {transcript_start:,}")

    # Extract show notes and transcript
    show_notes = full_text[:transcript_start].strip() if transcript_start > 0 else ""
    transcript = full_text[transcript_start:].strip()

    print(f"Show notes: {len(show_notes):,} chars")
    print(f"Transcript: {len(transcript):,} chars")

    # Split transcript into Part 1 and Part 2
    part1_transcript, part2_transcript = split_transcript(transcript)
    print(f"Part 1: {len(part1_transcript):,} chars")
    print(f"Part 2: {len(part2_transcript):,} chars")

    # Save markdown files
    save_markdown(episode_num, topic, guest, "Part 1", part1_transcript, pdf_url)
    save_markdown(episode_num, topic, guest, "Part 2", part2_transcript, pdf_url)

    # Save show notes as "Favorites" (since that's typically supplementary content)
    if show_notes:
        save_markdown(episode_num, topic, guest, "Favorites", show_notes, pdf_url)
    else:
        # Create minimal favorites
        save_markdown(episode_num, topic, guest, "Favorites",
                     f"Show notes and references for Episode {episode_num}: {topic}\n\nSee Part 1 and Part 2 for full transcript.",
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
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("All episodes processed!")
    print("="*60)


if __name__ == "__main__":
    main()
