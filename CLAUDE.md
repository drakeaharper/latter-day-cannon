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

### Scrape Follow Him Podcast
```bash
python3 scrape_followhim.py           # D&C 2025
python3 scrape_followhim_ot2026.py    # Old Testament 2026 + Thoughts to Keep in Mind
python3 scrape_followhim_bom2024.py   # Book of Mormon 2024
python3 scrape_followhim_nt2023.py    # New Testament 2023
python3 scrape_followhim_ot2022.py    # Old Testament 2022
python3 scrape_followhim_dc2021.py    # D&C 2021
python3 scrape_followhim_voices.py    # Voices of the Restoration
```
Scrapes show notes from the Follow Him podcast (followhim.co). Each scraper has an `EPISODES` list with episode numbers, topics, and URL slugs.

### Build Scripture Database
```bash
python3 build_scripture_database.py
```
Creates `docs/scripture-library.db` with all scripture data from markdown files. This is a **separate, read-only** database from the mind map database.

**Output (scripture-library.db):**
- 6 collections (OT, NT, BofM, D&C, PGP, Lectures on Faith)
- 88 books
- 1,589 chapters
- 42,351 verses
- 3,510 Topical Guide topics with 42,477 references
- 1,274 Bible Dictionary entries
- 2 General Conferences with 69 talks

**Output (followhim.db):**
- 8 series (D&C 2021, OT 2022, NT 2023, BofM 2024, D&C 2025, OT 2026, Voices of the Restoration, Thoughts to Keep in Mind)
- 279 episodes
- 811 parts (Part 1, Part 2, Favorites, or single episodes)

**Database Architecture:**
- `scripture-library.db` - Committed to repo, loaded from file (read-only reference data)
- `followhim.db` - Committed to repo, Follow Him podcast show notes
- `mind-map.db` - Stored in localStorage only (user's personal mind map data, NOT committed)

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

### Follow Him Scrapers (scrape_followhim*.py)
Scrapers for Follow Him podcast show notes from followhim.co:
- `EPISODES` list: Contains episode numbers, topics, and URL slugs for Part 1, Part 2, Favorites
- `extract_show_notes()`: Fetches and parses show note pages
- `extract_guest_from_transcript()`: Detects guest names from speaker attributions (handles titles like Dr., Pres., Sister, Brother, and suffixes like III, Jr.)
- `save_show_notes()`: Formats and writes to markdown file

**Regular series** (yearly Come Follow Me): Episodes have Part 1, Part 2, and Favorites files.

**Special series** (Voices of the Restoration, Thoughts to Keep in Mind): Single file per episode, stored in dedicated directories.

### Scripture Database Builder (build_scripture_database.py)
Builds SQLite database from all scraped markdown files for web viewer integration:
- `create_schema()`: Creates scripture tables in `docs/scripture-library.db`
- `populate_collections()`: Inserts 5 scripture collections
- `populate_books()`: Discovers and inserts 87 books from directory structure
- `parse_scripture_file()`: Parses markdown metadata, summary, and verses
- `populate_chapters_and_verses()`: Inserts all chapters and verses from markdown files
- `populate_topical_guide()`: Parses and inserts Topical Guide topics and references
- `populate_bible_dictionary()`: Parses and inserts Bible Dictionary entries

**Database Schema (scripture-library.db):**
- `scripture_collections`: 6 collections (OT, NT, BofM, D&C, PGP, Lectures on Faith)
- `scripture_books`: 88 books with collection relationships
- `scripture_chapters`: 1,589 chapters with summaries
- `scripture_verses`: 42,351 verses with full text
- `topical_guide_topics`: 3,510 topics
- `topical_guide_references`: 42,477 scripture references
- `bible_dictionary_entries`: 1,274 encyclopedic entries
- `general_conference_conferences`: Conference metadata
- `general_conference_talks`: Conference talk content

**Database Schema (followhim.db):**
- `followhim_series`: 8 series with year and scripture focus
- `followhim_episodes`: 279 episodes with titles and scripture references
- `followhim_parts`: 811 parts with guest, content, and URLs

**Separation of Concerns:**
- Scripture database (`scripture-library.db`) is committed to repository
- Follow Him database (`followhim.db`) is committed to repository
- Mind map database (`mind-map.db`) stays in browser localStorage only
- No conflicts when users pull updates to reference data

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

followhim/
├── doctrine-and-covenants-2021/
├── old-testament-2022/
├── new-testament-2023/
├── book-of-mormon-2024/
├── doctrine-and-covenants-2025/
├── old-testament-2026/
├── voices-of-the-restoration/
└── thoughts-to-keep-in-mind/
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

**Follow Him (Regular Episodes)**: `[Episode XX][Topic][Part].md`

Examples:
- `[Episode 01][Introduction to the Old Testament][Part 1].md`
- `[Episode 05][Genesis 5 Moses 6][Favorites].md`
- `[Episode 52][Christmas][Part 2].md`

**Follow Him (Special Series)**: `[Episode XX][Topic].md`

Examples (Voices of the Restoration, Thoughts to Keep in Mind):
- `[Episode 01][Joseph Smith's Family].md`
- `[Episode 01][Reading the Old Testament].md`

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

**Follow Him Files (Regular Episodes)**:
```
Episode: 1
Topic: Introduction to the Old Testament
Part: Part 1
Guest: Dr. Joshua Sears
URL: [Source URL]

---

# [Episode Title]

[Transcript with speaker attributions and timestamps]
Speaker Name: 00:00 [Text...]
```

**Follow Him Files (Special Series)**:
```
Episode: 1
Series: Thoughts to Keep in Mind
Topic: Reading the Old Testament
Guest: Dr. Ross Baron
URL: [Source URL]

---

# [Episode Title]

[Transcript with speaker attributions and timestamps]
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

**Follow Him Podcast**:
- D&C 2021: 156 files (52 episodes × 3 parts)
- Old Testament 2022: 156 files
- New Testament 2023: 159 files
- Book of Mormon 2024: 156 files
- D&C 2025: 156 files
- Old Testament 2026: 15+ files (ongoing)
- Voices of the Restoration: 12 files
- Thoughts to Keep in Mind: 1+ files (ongoing)
- **Follow Him Total: ~811 files**

**Grand Total: ~7,181 files**

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

**Follow Him URLs** (followhim.co):
- Episode index: `https://followhim.co/old-testament-2026-episodes-1-10/`
- Show note pattern: `https://followhim.co/show-note/[slug]/`
- Slugs are typically numeric like `2-542` or descriptive like `doctrine-covenants-episode-23-2025-...`

## Local Development

The web application requires a local web server for development due to browser CORS restrictions on `file://` protocol.

**Why a server is needed:**
- The Scripture Library, Topical Guide, and Bible Dictionary pages use `fetch()` to load `scripture-library.db` (16MB)
- Browsers block `fetch()` requests on `file://` protocol for security
- Mind Map works locally because it stores its SQLite database in localStorage (no fetch required)
- Production (GitHub Pages) works fine because it serves over `https://`

**Start local development server:**
```bash
cd docs
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

**Alternative servers:**
```bash
# Node.js
npx serve

# PHP
php -S localhost:8000
```

**Database Architecture:**
Both the Mind Map and Scripture Library use SQLite databases via sql.js (WebAssembly):

1. **Mind Map Database** (`mind-map.db`)
   - Created in-memory with sql.js
   - Exported to Uint8Array and serialized to localStorage
   - Loaded from localStorage on page load
   - ✅ Works with `file://` protocol (no fetch needed)
   - User's personal data, NOT committed to repo

2. **Scripture Library Database** (`scripture-library.db`)
   - Pre-built 16MB SQLite file in `docs/` directory
   - Fetched from server and loaded into sql.js
   - ❌ Requires HTTP/HTTPS (fetch doesn't work with `file://`)
   - Read-only reference data, committed to repo
   - Shared by Scripture Library, Topical Guide, and Bible Dictionary

## Planning Documentation

See `planning/` directory for:
- `scraping-strategy.md` - Original scripture scraper implementation strategy
- `output-format-specification.md` - File format specification for scriptures
- `url-tree-structure.md` - URL patterns and navigation structure for scriptures
- `topical-guide-scraping-plan.md` - Topical Guide scraper implementation plan
- `bible-dictionary-scraping-plan.md` - Bible Dictionary scraper implementation plan
- `study-helps-integration-plan.md` - Study Helps landing page integration plan
