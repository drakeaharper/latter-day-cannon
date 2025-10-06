# Scripture Database Integration Plan

## Overview
Integrate all scraped scripture content into the existing mind-map database to create a unified LDS study application combining personal notes with scripture reference.

## Architecture Decision: Combined Database

### Rationale
- **Cross-linking**: Direct SQL joins between mind map nodes and scripture references
- **Unified search**: Search across personal notes and scriptures simultaneously
- **Annotation capability**: Users can create mind map nodes that reference specific verses
- **Single deployment**: One database file, simpler architecture
- **Future features**: Reading plans, cross-references, study sessions

### Data Separation Strategy
- **Separate tables**: Mind map tables vs. scripture tables (clear boundaries)
- **Reference data immutable**: Scripture content read-only after population
- **User data mutable**: Mind map nodes, edges, positions can be modified
- **Rebuild strategy**: Can repopulate scripture tables without touching user data

## Database Schema

### Existing Mind Map Tables
```sql
-- Keep existing mind map schema unchanged
nodes (id, title, content, x, y, created_at, updated_at)
edges (id, source_id, target_id, created_at)
```

### New Scripture Tables

#### Collections Table
```sql
CREATE TABLE scripture_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "Old Testament"
    abbreviation TEXT NOT NULL,            -- "OT"
    sort_order INTEGER NOT NULL,           -- For display ordering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Books Table
```sql
CREATE TABLE scripture_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    name TEXT NOT NULL,                    -- "Genesis"
    abbreviation TEXT,                     -- "Gen"
    sort_order INTEGER NOT NULL,           -- Order within collection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES scripture_collections(id)
);
```

#### Chapters Table
```sql
CREATE TABLE scripture_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,       -- 1, 2, 3... (or section number)
    title TEXT,                            -- Chapter heading
    summary TEXT,                          -- Chapter summary/introduction
    url TEXT NOT NULL,                     -- Source URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES scripture_books(id),
    UNIQUE (book_id, chapter_number)
);
```

#### Verses Table
```sql
CREATE TABLE scripture_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,         -- 1, 2, 3...
    text TEXT NOT NULL,                    -- Verse content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES scripture_chapters(id),
    UNIQUE (chapter_id, verse_number)
);

-- Full-text search index
CREATE VIRTUAL TABLE scripture_verses_fts USING fts5(
    text,
    content=scripture_verses,
    content_rowid=id
);
```

### Study Helps Tables

#### Topical Guide
```sql
CREATE TABLE topical_guide_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL UNIQUE,       -- "Baptism, Essential"
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE topical_guide_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    collection_name TEXT,                  -- "Book of Mormon"
    scripture_text TEXT,                   -- Excerpt from scripture
    citation TEXT,                         -- "1 Ne. 3:7"
    sort_order INTEGER,
    FOREIGN KEY (topic_id) REFERENCES topical_guide_topics(id)
);

CREATE TABLE topical_guide_see_also (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    reference TEXT NOT NULL,               -- "Baptism; Holy Ghost, Baptism of"
    FOREIGN KEY (topic_id) REFERENCES topical_guide_topics(id)
);
```

#### Bible Dictionary
```sql
CREATE TABLE bible_dictionary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_name TEXT NOT NULL UNIQUE,       -- "Baptism"
    body TEXT NOT NULL,                    -- Full entry content
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search index
CREATE VIRTUAL TABLE bible_dictionary_fts USING fts5(
    entry_name,
    body,
    content=bible_dictionary_entries,
    content_rowid=id
);
```

### Cross-Reference Tables (Future)

#### Scripture References from Mind Map Nodes
```sql
CREATE TABLE node_scripture_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL,
    verse_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (verse_id) REFERENCES scripture_verses(id),
    UNIQUE (node_id, verse_id)
);
```

## Data Population Strategy

### Phase 1: Schema Migration
1. Add scripture tables to existing database schema
2. Create indexes for performance
3. Set up FTS (full-text search) tables

### Phase 2: Populate Collections & Books
```python
# Hardcoded data - known structure
collections = [
    ("Old Testament", "OT", 1),
    ("New Testament", "NT", 2),
    ("Book of Mormon", "BofM", 3),
    ("Doctrine and Covenants", "D&C", 4),
    ("Pearl of Great Price", "PGP", 5)
]

# Parse from directory structure or hardcode
books = [
    # (collection_id, name, abbreviation, sort_order)
    (1, "Genesis", "Gen", 1),
    (1, "Exodus", "Ex", 2),
    # ... etc
]
```

### Phase 3: Parse Markdown Files
```python
# For each markdown file in scriptures/
# 1. Parse metadata header (Collection, Book, Chapter, Title, URL)
# 2. Extract summary paragraph
# 3. Extract verses (number + text)
# 4. Insert into database

def parse_scripture_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Extract header metadata
    metadata = parse_metadata(lines[:10])

    # Extract summary (text before verse 1)
    summary = extract_summary(lines)

    # Extract verses
    verses = extract_verses(lines)

    return {
        'collection': metadata['collection'],
        'book': metadata['book'],
        'chapter': metadata['chapter'],
        'title': metadata['title'],
        'url': metadata['url'],
        'summary': summary,
        'verses': verses
    }
```

### Phase 4: Parse Study Helps
```python
# Parse topical_guide/*.md files
def parse_topical_guide_file(filepath):
    # Extract topic name, see also references, scripture references
    pass

# Parse bible_dictionary/*.md files
def parse_bible_dictionary_file(filepath):
    # Extract entry name, body content
    pass
```

### Phase 5: Build Search Indexes
```python
# Populate FTS tables after main data loaded
INSERT INTO scripture_verses_fts(rowid, text)
SELECT id, text FROM scripture_verses;

INSERT INTO bible_dictionary_fts(rowid, entry_name, body)
SELECT id, entry_name, body FROM bible_dictionary_entries;
```

## Build Script Implementation

### File: `build_scripture_database.py`
```python
#!/usr/bin/env python3
"""
Populates scripture tables in mind-map.db from scraped markdown files.

Usage:
    python3 build_scripture_database.py
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime

class ScriptureDatabaseBuilder:
    def __init__(self, db_path='mind-map.db', scriptures_dir='scriptures'):
        self.db_path = db_path
        self.scriptures_dir = Path(scriptures_dir)
        self.conn = None

    def build(self):
        """Main build process"""
        self.connect()
        self.create_schema()
        self.populate_collections()
        self.populate_books()
        self.populate_chapters_and_verses()
        self.populate_topical_guide()
        self.populate_bible_dictionary()
        self.build_search_indexes()
        self.close()

    def create_schema(self):
        """Create all scripture tables"""
        pass

    def populate_chapters_and_verses(self):
        """Parse all markdown files and insert data"""
        for md_file in self.scriptures_dir.rglob('*.md'):
            data = self.parse_scripture_file(md_file)
            self.insert_chapter(data)

    def parse_scripture_file(self, filepath):
        """Parse individual scripture markdown file"""
        pass
```

## UI Integration

### New UI Components

#### 1. Scripture Browser Panel
- Collection dropdown (OT, NT, BofM, D&C, PGP)
- Book dropdown (filtered by collection)
- Chapter dropdown (filtered by book)
- Display selected chapter with verses

#### 2. Scripture Search
- Full-text search across all verses
- Filter by collection/book
- Display results with context

#### 3. Study Helps Browser
- Topical Guide search and browse
- Bible Dictionary search and browse
- Cross-reference navigation

#### 4. Integration with Mind Map
- "Link to Scripture" button on nodes
- Display linked verses on node selection
- Create new node from verse (quote scripture)

### Navigation Flow
```
Main App
├── Mind Map Canvas (existing)
│   └── Nodes can reference scripture verses
├── Scripture Browser (new)
│   ├── Browse by Collection > Book > Chapter
│   └── Read verses
├── Scripture Search (new)
│   └── Full-text search across all scriptures
└── Study Helps (new)
    ├── Topical Guide
    └── Bible Dictionary
```

## Performance Considerations

### Database Size Estimates
- **Scripture content**: ~1,589 chapters × ~20 verses avg = ~32K verses
- **Verse text**: ~100 bytes avg × 32K = ~3.2 MB
- **Topical Guide**: ~3,512 topics × ~10 refs avg = ~1 MB
- **Bible Dictionary**: ~1,274 entries × ~500 bytes avg = ~0.6 MB
- **Indexes and metadata**: ~1 MB
- **Total estimated**: ~6-8 MB for all scripture data

### Query Optimization
- Index on `(book_id, chapter_number)` for chapter lookup
- Index on `(chapter_id, verse_number)` for verse lookup
- FTS5 indexes for search performance
- Consider materializing common queries (e.g., verse reference lookup)

### Lazy Loading Strategy
- Load collections/books metadata on app start
- Load chapter content on demand
- Load search results on demand
- Cache recently viewed chapters

## Deployment Strategy

### Build Process
```bash
# 1. Run scripture database builder
python3 build_scripture_database.py

# 2. Output: Updated mind-map.db with scripture data

# 3. Deploy updated database to GitHub Pages
cp mind-map.db public/
git add public/mind-map.db
git commit -m "Update scripture database"
git push
```

### Update Strategy (Future)
```bash
# To update scriptures without losing user's mind map:
# 1. Export user tables
# 2. Rebuild scripture tables
# 3. Import user tables back
# Or: Use separate SQL transactions to DELETE/INSERT only scripture tables
```

## Implementation Phases

### Phase 1: Database Schema (Week 1)
- [ ] Add scripture tables to schema
- [ ] Create migration script
- [ ] Test schema with sample data

### Phase 2: Data Population (Week 1)
- [ ] Implement markdown parser
- [ ] Populate scripture tables from files
- [ ] Populate study helps tables
- [ ] Build search indexes

### Phase 3: UI - Basic Browser (Week 2)
- [ ] Collection/Book/Chapter dropdowns
- [ ] Chapter display component
- [ ] Basic navigation

### Phase 4: UI - Search (Week 2)
- [ ] Full-text search UI
- [ ] Search results display
- [ ] Topical Guide browser
- [ ] Bible Dictionary browser

### Phase 5: Integration (Week 3)
- [ ] Link mind map nodes to verses
- [ ] Display verse references on nodes
- [ ] Create node from verse
- [ ] Cross-reference navigation

### Phase 6: Polish (Week 3)
- [ ] Responsive design
- [ ] Performance optimization
- [ ] Documentation
- [ ] Testing

## Success Criteria

### Functional Requirements
- ✅ All 1,589 scripture chapters loaded and queryable
- ✅ All study helps (Topical Guide, Bible Dictionary) loaded
- ✅ Full-text search works across all content
- ✅ Navigation: Collection → Book → Chapter works smoothly
- ✅ Mind map integration: Can link nodes to verses

### Performance Requirements
- ✅ Database loads in <2 seconds
- ✅ Chapter navigation instant (<100ms)
- ✅ Search results return in <500ms
- ✅ Total database size <20 MB

### Quality Requirements
- ✅ All text properly encoded (UTF-8)
- ✅ Verse numbering accurate
- ✅ No missing chapters/verses
- ✅ Cross-references preserved

## Next Steps
1. Review and approve this plan
2. Create database schema migration script
3. Implement markdown parser and population script
4. Test with sample data
5. Build out UI components
6. Deploy and iterate
