# Bible Dictionary Scraping Plan

## Overview

The Bible Dictionary is a comprehensive reference guide providing encyclopedic entries about biblical terms, people, places, and concepts. Unlike the Topical Guide which focuses on scripture cross-references, the Bible Dictionary provides detailed explanatory text about each entry.

## URL Structure Analysis

### Entry Point
- **Main Index**: `https://www.churchofjesuschrist.org/study/scriptures/bd?lang=eng`
- **Introduction**: `https://www.churchofjesuschrist.org/study/scriptures/bd/introduction?lang=eng`

### Entry URLs
- **Pattern**: `/study/scriptures/bd/[entry-slug]?lang=eng`
- **Examples**:
  - Aaron: `/study/scriptures/bd/aaron?lang=eng`
  - Baptism: `/study/scriptures/bd/baptism?lang=eng`
  - Abraham, Covenant of: `/study/scriptures/bd/abraham-covenant-of?lang=eng`

### Organization
- **Alphabetical**: Entries organized A-Z
- **Single topic per entry**: Each entry is a standalone article
- **No sub-categories**: Unlike Topical Guide, no hierarchical structure

## Content Structure

### Entry Page Elements

1. **Entry Title**: Main heading (e.g., "Aaron", "Baptism")
2. **Body Text**: Single or multiple paragraphs of encyclopedic content
3. **Scripture References**: May include inline scripture citations
4. **Cross-references**: Some entries reference other Bible Dictionary entries

### Example Entry Structure (Aaron)

```
Title: Aaron

Son of Amram and Jochebed, of the tribe of Levi (Ex. 6:16–20); elder brother of
Moses (Ex. 7:7). He was appointed by the Lord to assist Moses in bringing the
children of Israel out of Egypt and to be his spokesman (Ex. 4:10–16, 27–31;
5:1–12:50). He was with Moses until the 40th year of the wanderings...

[Continues with detailed historical and doctrinal information]
```

### Example Entry Structure (Baptism)

```
Title: Baptism

From a Greek word meaning to "dip" or "immerse." Baptism in water is the
introductory ordinance of the gospel and must be followed by baptism of the
Spirit in order to be complete. As one of the ordinances of the gospel, it is
associated with faith in the Lord Jesus Christ, repentance, and the laying on
of hands for the gift of the Holy Ghost...

[Continues with detailed doctrinal explanation]
```

## Discovery Strategy

### Phase 1: Discover All Entries
1. Scrape main index page: `https://www.churchofjesuschrist.org/study/scriptures/bd?lang=eng`
2. Extract all entry links from alphabetical navigation
3. Build list of all entry URLs and titles
4. Estimated count: ~700-1,000 entries (TBD after discovery)

### Phase 2: Extract Entry Content
For each entry:
1. Fetch entry page
2. Extract:
   - Entry title
   - Full body text (all paragraphs)
   - Inline scripture references (if needed for formatting)

## Output Format Specification

### File Naming Convention
- Pattern: `[Entry Name].md`
- Examples:
  - `Aaron.md`
  - `Baptism.md`
  - `Abraham, Covenant of.md`

### Directory Structure
```
study_helps/
├── topical_guide/
└── bible_dictionary/
    ├── Aaron.md
    ├── Baptism.md
    ├── Abraham, Covenant of.md
    └── ... (all entries)
```

### Markdown File Format

```markdown
Entry: [Entry Name]
URL: [Source URL]

---

[Full text content of the entry, preserving paragraph breaks]
```

### Example Output File

**File**: `study_helps/bible_dictionary/Baptism.md`

```markdown
Entry: Baptism
URL: https://www.churchofjesuschrist.org/study/scriptures/bd/baptism?lang=eng

---

From a Greek word meaning to "dip" or "immerse." Baptism in water is the
introductory ordinance of the gospel and must be followed by baptism of the
Spirit in order to be complete. As one of the ordinances of the gospel, it is
associated with faith in the Lord Jesus Christ, repentance, and the laying on
of hands for the gift of the Holy Ghost. Baptism has always been practiced
whenever the gospel of Jesus Christ has been on the earth and has been taught
by men holding the holy priesthood who could administer the ordinances...

[Full entry text continues]
```

## Implementation Plan

### Core Scraper Class: `BibleDictionaryScraper`

**Key Methods:**

1. `discover_entries()`:
   - Scrape main index page
   - Extract all entry links from alphabetical navigation
   - Return list of (entry_name, entry_url) tuples

2. `extract_entry_content(entry_url)`:
   - Fetch entry page HTML
   - Extract entry title
   - Extract all body paragraphs
   - Combine paragraphs into full text
   - Return structured data

3. `clean_text(text)`:
   - Normalize whitespace
   - Preserve paragraph breaks
   - Handle special characters
   - Return cleaned text

4. `save_entry(entry_data, output_dir)`:
   - Format entry data as markdown
   - Save to appropriate file in `study_helps/bible_dictionary/`

5. `scrape_all()`:
   - Orchestrate full scraping process
   - Discover all entries
   - Extract and save each entry
   - Log progress

### Rate Limiting & Error Handling

- **Rate Limiting**: 2-second delay between requests (same as other scrapers)
- **Retry Logic**: Retry failed requests up to 3 times with 5-second delays
- **Error Logging**: Log failed entries for manual review
- **Progress Tracking**: Log to both console and `bible_dictionary_scraping.log`

### HTML Parsing Strategy

The page uses React/dynamic content, but content is server-rendered. Key selectors:

1. **Navigation Links** (for discovery):
   - Look for `<a>` tags with `href="/study/scriptures/bd/[entry-slug]?lang=eng"`
   - Extract from table of contents navigation structure

2. **Entry Title**:
   - Primary `<h1>` or title element in main content area

3. **Body Content**:
   - Find `<div class="body">` element
   - Extract all `<p>` tags
   - Preserve paragraph breaks between paragraphs

### Dependencies

Same as other scrapers:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `logging` - Progress tracking
- `pathlib` - File management

## Comparison with Topical Guide

| Aspect | Topical Guide | Bible Dictionary |
|--------|---------------|------------------|
| Purpose | Scripture cross-references | Encyclopedic explanations |
| Content | Lists of scripture citations | Prose paragraphs |
| Format | Bulleted scripture references | Continuous text |
| Length | Usually brief | Can be extensive |
| Organization | Alphabetical topics | Alphabetical entries |
| See Also | Yes, cross-references | May reference other entries |

## Estimated Output

- **Entry Count**: ~700-1,000 entries (to be confirmed after discovery)
- **Output Directory**: `study_helps/bible_dictionary/`
- **File Format**: Individual markdown files, one per entry
- **Naming**: Based on exact entry title from website

## Testing Strategy

Before full scrape:

1. **Test Discovery**: Run discovery on main index, verify entry count
2. **Test Sample Entries**: Extract 3-5 diverse entries:
   - Short entry (e.g., "Aaron")
   - Long entry (e.g., "Baptism")
   - Entry with special characters or punctuation
   - Entry with extensive scripture citations
3. **Verify Output Format**: Ensure markdown formatting is clean and readable

## Similarities to Topical Guide Scraper

- Same base URL structure pattern
- Same alphabetical organization
- Same rate limiting and retry logic
- Same file naming conventions (by entry name)
- Can reuse much of the TopicalGuideScraper code structure

## Key Differences from Topical Guide Scraper

- **Content Type**: Full prose text vs. bulleted scripture references
- **Extraction**: Single body div with paragraphs vs. organized by collection
- **Formatting**: Continuous text vs. organized sections
- **Simpler Structure**: No "See Also" section, no collection grouping

## Next Steps

1. Create `scrape_bible_dictionary.py` script
2. Implement `BibleDictionaryScraper` class (can borrow from TopicalGuideScraper)
3. Test discovery and extraction on sample entries
4. Run full scrape
5. Verify output quality
6. Update CLAUDE.md documentation
