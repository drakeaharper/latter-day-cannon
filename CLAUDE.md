# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web scraper for LDS canonical scriptures and study helps from churchofjesuschrist.org. Extracts all scripture text from five collections (Old Testament, New Testament, Book of Mormon, Doctrine and Covenants, Pearl of Great Price) plus the Topical Guide, and formats them for LLM analysis.

## Running the Scrapers

### Run All Collections
```bash
python3 scrape_all_scriptures.py
```

### Run Individual Collections
```bash
python3 scrape_ot.py        # Old Testament
python3 scrape_nt.py        # New Testament
python3 scrape_bofm.py      # Book of Mormon
python3 scrape_dc.py        # Doctrine and Covenants
python3 scrape_pgp.py       # Pearl of Great Price
```

### Run Collections in Parallel
```bash
python3 scrape_parallel.py   # Launches multiple scrapers concurrently
python3 launch_parallel.py   # Simple parallel launcher
```

### Generate Combined Files for NotebookLM
```bash
python3 create_combined_files.py
```
Creates 9 combined files in `notebooklm/` directory (under 50-file limit).

### Test Extraction Logic
```bash
python3 test_extraction.py
```
Tests verse extraction on Moses Chapter 1 before running full scrape.

### Scrape Topical Guide
```bash
python3 scrape_topical_guide.py
```
Scrapes all topics from the LDS Topical Guide (~3,512 topics).

### Scrape Bible Dictionary
```bash
python3 scrape_bible_dictionary.py
```
Scrapes all entries from the LDS Bible Dictionary (~1,274 entries).

## Architecture

### Core Scraping Flow
1. **Discovery Phase**: Scrape collection page → discover books → discover chapters
2. **Extraction Phase**: For each chapter, extract title, summary, and verses
3. **Formatting Phase**: Save to markdown files with consistent structure
4. **Combination Phase**: Merge individual files into larger collections

### ScriptureScraper Class (scrape_all_scriptures.py)
Central scraper with these key methods:
- `discover_books()`: Finds all books in a collection by parsing navigation links
- `discover_chapters()`: Extracts chapter URLs from book table of contents
- `extract_chapter_content()`: Parses HTML to extract title, summary, and verses
- `clean_verse_text()`: Removes study notes and markup while preserving text
- `save_chapter()`: Formats and writes to markdown file

### Individual Scrapers
Each collection has a dedicated scraper (`scrape_ot.py`, `scrape_nt.py`, etc.) with:
- Hardcoded book abbreviations and chapter counts for reliability
- Collection-specific configuration (e.g., D&C uses "sections" not "chapters")
- Same core extraction logic as `ScriptureScraper`

### Parallel Execution
`scrape_parallel.py` launches multiple collection scrapers as subprocesses and monitors progress.

### Topical Guide Scraper (scrape_topical_guide.py)
Scraper for LDS Topical Guide with these key methods:
- `discover_topics()`: Scrapes index page to find all topic URLs (~3,512 topics)
- `extract_topic_content()`: Parses topic page to extract title, "See Also" references, and scripture references
- `save_topic()`: Formats and writes topic to markdown file

### Bible Dictionary Scraper (scrape_bible_dictionary.py)
Scraper for LDS Bible Dictionary with these key methods:
- `discover_entries()`: Scrapes index page to find all entry URLs (~1,274 entries)
- `extract_entry_content()`: Parses entry page to extract title and full body text
- `save_entry()`: Formats and writes entry to markdown file

## Data Organization

### Directory Structure
```
scriptures/
├── old-testament/
├── new-testament/
├── book-of-mormon/
├── doctrine-and-covenants/
└── pearl-of-great-price/

study_helps/
├── topical_guide/
└── bible_dictionary/
```

### File Naming Convention

**Scriptures**: `[Collection][Book][Chapter/Section].md`

Examples:
- `[Old Testament][Genesis][Chapter 1].md`
- `[Doctrine and Covenants][Section 1].md`
- `[Book of Mormon][1 Nephi][Chapter 3].md`

**Topical Guide**: `[Topic Name].md`

Examples:
- `Baptism.md`
- `Baptism, Essential.md`
- `Abrahamic Covenant.md`

**Bible Dictionary**: `[Entry Name].md`

Examples:
- `Baptism.md`
- `Abraham.md`
- `Acts of the Apostles.md`

### File Format

**Scripture Files**:
```
Collection: Old Testament
Book: Genesis
Chapter: 1
Title: [Chapter title]
URL: [Source URL]

---

[Chapter summary if available]

1 [Verse text]

2 [Verse text]
```

**Topical Guide Files**:
```
Topic: [Topic Name]
URL: [Source URL]

---

## See Also

[Cross-reference 1]; [Cross-reference 2]; ...

---

## New Testament

- [Scripture excerpt], [Citation]
- [Scripture excerpt], [Citation]

## Book of Mormon

- [Scripture excerpt], [Citation]
```

**Bible Dictionary Files**:
```
Entry: [Entry Name]
URL: [Source URL]

---

[Full encyclopedic text content with paragraph breaks preserved]
```

## Key Implementation Details

### Rate Limiting
All scrapers use 2-second delays between requests (`time.sleep(2)`) to avoid overloading the server.

### Retry Logic
`fetch_page()` method retries failed requests up to 3 times with 5-second delays.

### Text Cleaning
The `clean_verse_text()` method:
1. Extracts and removes verse numbers
2. Removes study note reference links but preserves their text
3. Removes superscript elements
4. Normalizes whitespace

### Doctrine & Covenants Special Handling
Uses "Section" instead of "Chapter" and has different URL patterns (`/dc-testament/dc/[number]`).

### Progress Tracking
All scrapers log to both console and dedicated log files:
- `scripture_scraping.log` (all collections)
- `ot_scraping.log`, `nt_scraping.log`, etc. (individual collections)
- `topical_guide_scraping.log` (Topical Guide)
- `bible_dictionary_scraping.log` (Bible Dictionary)

### Estimated File Counts
**Scriptures**:
- Old Testament: ~929 chapters
- New Testament: ~260 chapters
- Book of Mormon: ~239 chapters
- Doctrine & Covenants: ~140 sections
- Pearl of Great Price: ~16 chapters
- **Scriptures Total: ~1,584 files**

**Study Helps**:
- Topical Guide: ~3,512 topics
- Bible Dictionary: ~1,274 entries
- **Study Helps Total: ~4,786 files**

**Grand Total: ~6,370 files**

## Dependencies

Required Python packages:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `logging` - Progress tracking
- `pathlib` - File management

Install with:
```bash
pip install requests beautifulsoup4
```

## NotebookLM Integration

The `create_combined_files.py` script combines individual chapter files into 9 large files optimized for NotebookLM's 50-file limit:

1. Pearl of Great Price (complete)
2. Doctrine and Covenants (complete)
3. New Testament (complete)
4. Book of Mormon (complete)
5-9. Old Testament split into 5 parts: Law, History, Poetry, Major Prophets, Minor Prophets

Output directory: `notebooklm/`

## URL Structure

Base URL: `https://www.churchofjesuschrist.org`

**Scripture Collection URLs**:
- Old Testament: `/study/scriptures/ot?lang=eng`
- New Testament: `/study/scriptures/nt?lang=eng`
- Book of Mormon: `/study/scriptures/bofm?lang=eng`
- D&C: `/study/scriptures/dc-testament?lang=eng`
- Pearl of Great Price: `/study/scriptures/pgp?lang=eng`

Chapter URL pattern: `/study/scriptures/[collection]/[book]/[chapter]?lang=eng`

**Topical Guide URLs**:
- Index: `/study/scriptures/tg?lang=eng`
- Topic pattern: `/study/scriptures/tg/[topic-slug]?lang=eng`

**Bible Dictionary URLs**:
- Index: `/study/scriptures/bd?lang=eng`
- Entry pattern: `/study/scriptures/bd/[entry-slug]?lang=eng`

## Planning Documentation

See `planning/` directory for:
- `scraping-strategy.md` - Original scripture scraper implementation strategy
- `output-format-specification.md` - File format specification for scriptures
- `url-tree-structure.md` - URL patterns and navigation structure for scriptures
- `topical-guide-scraping-plan.md` - Topical Guide scraper implementation plan
- `bible-dictionary-scraping-plan.md` - Bible Dictionary scraper implementation plan
