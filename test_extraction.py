#!/usr/bin/env python3
"""
Test script to verify extraction logic works correctly
Tests on Moses Chapter 1 before running full scraping
"""

import requests
from bs4 import BeautifulSoup
import re

def test_extraction():
    """Test extraction on Moses Chapter 1"""
    url = "https://www.churchofjesuschrist.org/study/scriptures/pgp/moses/1?lang=eng"

    print(f"Testing extraction on: {url}")
    print("-" * 60)

    # Fetch the page
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title_element = soup.find('h1')
    title = title_element.get_text().strip() if title_element else "No title found"
    print(f"Title: {title}")

    # Extract summary
    summary_element = soup.find('p', class_='study-summary')
    summary = summary_element.get_text().strip() if summary_element else "No summary found"
    print(f"Summary: {summary[:100]}...")

    # Extract verses
    verse_elements = soup.find_all('p', class_='verse')
    print(f"Found {len(verse_elements)} verse elements")

    # Test first few verses
    for i, verse_element in enumerate(verse_elements[:3]):
        # Show original HTML structure
        print(f"\nOriginal HTML for verse {i+1}:")
        print(str(verse_element)[:200] + "...")

        verse_copy = verse_element.__copy__()

        # Extract verse number first
        verse_num_span = verse_copy.find('span', class_='verse-number')
        if verse_num_span:
            verse_num = verse_num_span.get_text().strip()
            verse_num_span.decompose()
        else:
            verse_num = "?"

        # Remove study note references but preserve the text they contain
        for note_ref in verse_copy.find_all('a', class_='study-note-ref'):
            # Replace the link with just its text content
            note_ref.replace_with(note_ref.get_text())

        # Remove any remaining sup elements (superscript references)
        for sup in verse_copy.find_all('sup'):
            sup.decompose()

        # Get remaining text
        verse_text = verse_copy.get_text().strip()
        verse_text = re.sub(r'\s+', ' ', verse_text)

        print(f"Extracted - Verse {verse_num}: {verse_text[:100]}...")

    print(f"\n{'-' * 60}")
    print("Extraction test complete!")

if __name__ == "__main__":
    test_extraction()