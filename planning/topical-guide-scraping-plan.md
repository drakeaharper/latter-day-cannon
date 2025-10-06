# Topical Guide Scraping Plan

## Overview

The Topical Guide is a comprehensive scripture reference system organized alphabetically by topic. Each topic contains scripture references from all five standard works (Old Testament, New Testament, Book of Mormon, Doctrine & Covenants, Pearl of Great Price).

## URL Structure Analysis

### Entry Point
- **Main Index**: `https://www.churchofjesuschrist.org/study/scriptures/tg?lang=eng`
- **Introduction**: `https://www.churchofjesuschrist.org/study/scriptures/tg/introduction?lang=eng`

### Topic Entry URLs
- **Pattern**: `/study/scriptures/tg/[topic-slug]?lang=eng`
- **Examples**:
  - Aaron: `/study/scriptures/tg/aaron?lang=eng`
  - Baptism: `/study/scriptures/tg/baptism?lang=eng`
  - Abrahamic Covenant: `/study/scriptures/tg/abrahamic-covenant?lang=eng`

### Organization
- **Alphabetical**: Topics organized A-Z
- **See Also References**: Many topics include cross-references to related topics
- **Sub-topics**: Some topics have specific sub-categories (e.g., "Baptism, Essential", "Baptism, Immersion")

## Content Structure

### Topic Entry Page Elements

1. **Topic Title**: Main heading (e.g., "Baptism")
2. **See Also Section**: Cross-references to related topics
3. **Scripture References**: Organized by collection
   - Old Testament
   - New Testament
   - Book of Mormon
   - Doctrine & Covenants
   - Pearl of Great Price
4. **Bible Dictionary Reference**: Some topics link to Bible Dictionary (BD)

### Scripture Reference Format
Each reference includes:
- Brief text excerpt from the scripture
- Scripture citation (e.g., "Matt. 3:16", "1 Ne. 20:1", "D&C 13")
- Hyperlink to full scripture passage

### Example Entry Structure (Baptism)

```
Title: Baptism

See also: Baptism, Essential; Baptism, Immersion; Baptism, Qualifications for;
Baptism for the Dead; Covenants; Jesus Christ, Baptism of; BD Baptism

[New Testament]
- Jesus, when he was baptized, Matt. 3:16.
- baptizing them in the name of the Father, Matt. 28:19.
- believeth and is baptized shall be saved, Mark 16:16.
...

[Book of Mormon]
- waters of Judah, or … of baptism, 1 Ne. 20:1.
- Lamb of God … baptized by water, 2 Ne. 31:5.
...

[Doctrine & Covenants]
- I confer … keys … of baptism, D&C 13.
...

[Pearl of Great Price]
- be born again … of water, Moses 6:59.
...
```

## Discovery Strategy

### Phase 1: Discover All Topics
1. Scrape main index page: `https://www.churchofjesuschrist.org/study/scriptures/tg?lang=eng`
2. Extract all topic links from navigation (organized by letter A-Z)
3. Build list of all topic URLs and titles
4. Estimated count: ~1,000-2,000 topics (TBD after discovery)

### Phase 2: Extract Topic Content
For each topic:
1. Fetch topic page
2. Extract:
   - Topic title
   - "See Also" cross-references
   - Scripture references grouped by collection (OT, NT, BofM, D&C, PGP)
   - Each reference's text excerpt and citation

## Output Format Specification

### File Naming Convention
- Pattern: `[Topic Name].md`
- Examples:
  - `Aaron.md`
  - `Baptism.md`
  - `Baptism, Essential.md`
  - `Abrahamic Covenant.md`

### Directory Structure
```
study_helps/
└── topical_guide/
    ├── Aaron.md
    ├── Aaron, Descendants of.md
    ├── Aaronic Priesthood.md
    ├── Baptism.md
    ├── Baptism, Essential.md
    └── ... (all topics)
```

### Markdown File Format

```markdown
Topic: [Topic Name]
URL: [Source URL]

---

## See Also

[Cross-reference topic 1]; [Cross-reference topic 2]; [etc.]

---

## New Testament

- [Brief text excerpt], [Scripture Citation]
- [Brief text excerpt], [Scripture Citation]

## Book of Mormon

- [Brief text excerpt], [Scripture Citation]

## Doctrine and Covenants

- [Brief text excerpt], [Scripture Citation]

## Pearl of Great Price

- [Brief text excerpt], [Scripture Citation]

## Old Testament

- [Brief text excerpt], [Scripture Citation]
```

### Example Output File

**File**: `study_helps/topical_guide/Baptism.md`

```markdown
Topic: Baptism
URL: https://www.churchofjesuschrist.org/study/scriptures/tg/baptism?lang=eng

---

## See Also

Baptism, Essential; Baptism, Immersion; Baptism, Qualifications for; Baptism for the Dead; Covenants; Jesus Christ, Baptism of; Jesus Christ, Taking the Name of; Jesus Christ, Types of, in Memory; Salvation for the Dead; BD Baptism

---

## New Testament

- Jesus, when he was baptized, Matt. 3:16.
- baptizing them in the name of the Father, Matt. 28:19.
- John did … preach the baptism of repentance for the remission of sins, Mark 1:4.
- baptized of John in Jordan, Mark 1:9 (Luke 3:3).
- believeth and is baptized shall be saved, Mark 16:16.
- Except a man be born of water, John 3:5.

## Book of Mormon

- waters of Judah, or … of baptism, 1 Ne. 20:1.
- Lamb of God … baptized by water, 2 Ne. 31:5.
- gate … is repentance and baptism by water, 2 Ne. 31:17.

## Doctrine and Covenants

- I confer … keys … of baptism, D&C 13.
- remission of sins by baptism, D&C 19:31.

## Pearl of Great Price

- be born again … of water, Moses 6:59.
```

## Implementation Plan

### Core Scraper Class: `TopicalGuideScraper`

**Key Methods:**

1. `discover_topics()`:
   - Scrape main index page
   - Extract all topic links from alphabetical navigation
   - Return list of (topic_name, topic_url) tuples

2. `extract_topic_content(topic_url)`:
   - Fetch topic page HTML
   - Extract topic title
   - Extract "See Also" references
   - Extract scripture references by collection
   - Return structured data

3. `clean_reference_text(text)`:
   - Remove HTML artifacts
   - Normalize whitespace
   - Preserve ellipses (…) and special characters
   - Return cleaned text

4. `save_topic(topic_data, output_dir)`:
   - Format topic data as markdown
   - Save to appropriate file in `study_helps/topical_guide/`

5. `scrape_all()`:
   - Orchestrate full scraping process
   - Discover all topics
   - Extract and save each topic
   - Log progress

### Rate Limiting & Error Handling

- **Rate Limiting**: 2-second delay between requests (same as scripture scraper)
- **Retry Logic**: Retry failed requests up to 3 times with 5-second delays
- **Error Logging**: Log failed topics for manual review
- **Progress Tracking**: Log to both console and `topical_guide_scraping.log`

### HTML Parsing Strategy

The page uses React/dynamic content, but content is server-rendered. Key selectors:

1. **Navigation Links** (for discovery):
   - Look for `<a>` tags with `href="/study/scriptures/tg/[topic-slug]?lang=eng"`
   - Extract from table of contents navigation structure

2. **Topic Title**:
   - Primary `<h1>` or title element in main content area

3. **See Also Section**:
   - Look for "See also" heading or section
   - Extract all linked topics

4. **Scripture References**:
   - Group by collection (may be in separate sections or all together)
   - Extract reference text and citation
   - Parse scripture links to get book/chapter/verse info

### Dependencies

Same as scripture scraper:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `logging` - Progress tracking
- `pathlib` - File management

## Estimated Output

- **Topic Count**: ~1,000-2,000 entries (to be confirmed after discovery)
- **Output Directory**: `study_helps/topical_guide/`
- **File Format**: Individual markdown files, one per topic
- **Naming**: Based on exact topic title from website

## Testing Strategy

Before full scrape:

1. **Test Discovery**: Run discovery on main index, verify topic count seems reasonable
2. **Test Sample Topics**: Extract 3-5 diverse topics:
   - Simple topic (e.g., "Aaron")
   - Complex topic with many references (e.g., "Baptism")
   - Topic with sub-categories (e.g., "Baptism, Essential")
   - Topic with special characters or punctuation
3. **Verify Output Format**: Ensure markdown formatting is clean and readable

## Next Steps

1. Create `scrape_topical_guide.py` script
2. Implement `TopicalGuideScraper` class
3. Test discovery and extraction on sample topics
4. Run full scrape
5. Verify output quality
6. Document in CLAUDE.md
