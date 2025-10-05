# Web Scraping Strategy

## Overview
Systematic approach to scrape all canonical scriptures from churchofjesuschrist.org and organize them for LLM analysis.

## Phase 1: Discovery and Mapping

### 1.1 Collection Discovery
- Start from: `https://www.churchofjesuschrist.org/study/scriptures?lang=eng&platform=web`
- Extract links to each collection:
  - Old Testament (`/study/scriptures/ot?lang=eng`)
  - New Testament (`/study/scriptures/nt?lang=eng`)
  - Book of Mormon (`/study/scriptures/bofm?lang=eng`)
  - Doctrine and Covenants (`/study/scriptures/dc-testament?lang=eng`)
  - Pearl of Great Price (`/study/scriptures/pgp?lang=eng`)

### 1.2 Book Discovery
For each collection:
- Parse the collection page to extract all book links
- Extract book abbreviations and full names
- Build mapping of book names to URL patterns

### 1.3 Chapter Discovery
For each book:
- Parse the book's table of contents
- Extract all chapter/section numbers
- Build complete URL list for all chapters

## Phase 2: Content Scraping

### 2.1 Rate Limiting
- Implement delays between requests (1-2 seconds minimum)
- Respect robots.txt if present
- Consider using session management for consistency

### 2.2 Error Handling
- Retry failed requests (max 3 attempts)
- Log all errors with URL and error details
- Continue scraping other content if individual chapters fail

### 2.3 Content Extraction
For each chapter page:
```python
# Pseudo-code for extraction logic
def extract_chapter_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Extract metadata
    collection = extract_collection_name(url)
    book = extract_book_name(soup)
    chapter = extract_chapter_number(url)
    title = extract_chapter_title(soup)

    # Extract verses
    verses = []
    verse_elements = soup.find_all('p', class_='verse')

    for verse_element in verse_elements:
        verse_number = verse_element.find('span', class_='verse-number').get_text()
        verse_text = clean_verse_text(verse_element)
        verses.append((verse_number, verse_text))

    return format_content(collection, book, chapter, title, verses)
```

## Phase 3: Data Organization

### 3.1 Directory Structure Creation
```bash
mkdir -p scriptures/{old-testament,new-testament,book-of-mormon,doctrine-and-covenants,pearl-of-great-price}
```

### 3.2 File Naming and Storage
- Use consistent naming: `[Collection][Book][Chapter].txt`
- Store in appropriate subdirectories
- Generate index files for each collection

## Implementation Tools

### Required Libraries
- `requests` or `httpx` for HTTP requests
- `BeautifulSoup4` for HTML parsing
- `time` for rate limiting
- `logging` for error tracking
- `pathlib` for file management

### Script Structure
```
scraper/
├── main.py              # Main orchestration script
├── discovery.py         # Collection/book/chapter discovery
├── extractor.py         # Content extraction logic
├── formatter.py         # Output formatting
├── utils.py             # Utilities and helpers
└── config.py            # Configuration and constants
```

## Validation and Quality Assurance

### 3.1 Data Validation
- Verify all expected collections are present
- Check for missing chapters/sections
- Validate verse numbering consistency
- Ensure file naming conventions are followed

### 3.2 Content Quality Checks
- Remove HTML artifacts
- Verify text encoding (UTF-8)
- Check for truncated content
- Validate verse counts against known scripture structure

### 3.3 Completeness Verification
- Generate manifest of all scraped files
- Compare against expected scripture canon
- Identify any gaps or missing content

## Estimated Scope

### Content Volume
- Old Testament: ~39 books, ~929 chapters
- New Testament: ~27 books, ~260 chapters
- Book of Mormon: ~15 books, ~239 chapters
- Doctrine and Covenants: ~138 sections
- Pearl of Great Price: ~5 books, ~8 chapters

**Total Estimated**: ~1,573 individual files

### Processing Time
- With 2-second delays: ~52 minutes minimum
- Including discovery and processing: ~1-2 hours total

## Risk Mitigation

### 1. Server Load
- Implement conservative rate limiting
- Monitor for HTTP 429 responses
- Consider running during off-peak hours

### 2. Content Changes
- Timestamp all scraped content
- Store source URLs for verification
- Log any parsing errors for manual review

### 3. Technical Issues
- Implement robust error handling
- Create resumable scraping (checkpoint system)
- Generate detailed logs for debugging

## Next Steps
1. Implement discovery phase scripts
2. Test extraction logic on sample chapters
3. Build full scraping pipeline
4. Execute scraping with monitoring
5. Validate and organize output data