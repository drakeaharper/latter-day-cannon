-- Scripture Database Schema
-- Extends the existing mind map database with scripture tables

-- ============================================================================
-- SCRIPTURE COLLECTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS scripture_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "Old Testament"
    abbreviation TEXT NOT NULL,            -- "OT"
    sort_order INTEGER NOT NULL,           -- For display ordering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scripture_collections_sort
ON scripture_collections(sort_order);

-- ============================================================================
-- SCRIPTURE BOOKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS scripture_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    name TEXT NOT NULL,                    -- "Genesis"
    abbreviation TEXT,                     -- "Gen"
    sort_order INTEGER NOT NULL,           -- Order within collection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES scripture_collections(id)
);

CREATE INDEX IF NOT EXISTS idx_scripture_books_collection
ON scripture_books(collection_id, sort_order);

-- ============================================================================
-- SCRIPTURE CHAPTERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS scripture_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,       -- 1, 2, 3... (or section number for D&C)
    title TEXT,                            -- Chapter heading
    summary TEXT,                          -- Chapter summary/introduction
    url TEXT NOT NULL,                     -- Source URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES scripture_books(id),
    UNIQUE (book_id, chapter_number)
);

CREATE INDEX IF NOT EXISTS idx_scripture_chapters_book
ON scripture_chapters(book_id, chapter_number);

-- ============================================================================
-- SCRIPTURE VERSES
-- ============================================================================

CREATE TABLE IF NOT EXISTS scripture_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,         -- 1, 2, 3...
    text TEXT NOT NULL,                    -- Verse content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES scripture_chapters(id),
    UNIQUE (chapter_id, verse_number)
);

CREATE INDEX IF NOT EXISTS idx_scripture_verses_chapter
ON scripture_verses(chapter_id, verse_number);

-- Note: FTS5 (Full-Text Search) not available in standard sql.js
-- Will use LIKE queries or implement in-memory search

-- ============================================================================
-- TOPICAL GUIDE
-- ============================================================================

CREATE TABLE IF NOT EXISTS topical_guide_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL UNIQUE,       -- "Baptism, Essential"
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_topical_guide_topics_name
ON topical_guide_topics(topic_name);

CREATE TABLE IF NOT EXISTS topical_guide_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    collection_name TEXT,                  -- "Book of Mormon"
    scripture_text TEXT,                   -- Excerpt from scripture
    citation TEXT,                         -- "1 Ne. 3:7"
    sort_order INTEGER,
    FOREIGN KEY (topic_id) REFERENCES topical_guide_topics(id)
);

CREATE INDEX IF NOT EXISTS idx_topical_guide_references_topic
ON topical_guide_references(topic_id, sort_order);

CREATE TABLE IF NOT EXISTS topical_guide_see_also (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    reference TEXT NOT NULL,               -- "Baptism; Holy Ghost, Baptism of"
    FOREIGN KEY (topic_id) REFERENCES topical_guide_topics(id)
);

-- ============================================================================
-- BIBLE DICTIONARY
-- ============================================================================

CREATE TABLE IF NOT EXISTS bible_dictionary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_name TEXT NOT NULL UNIQUE,       -- "Baptism"
    body TEXT NOT NULL,                    -- Full entry content
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bible_dictionary_entries_name
ON bible_dictionary_entries(entry_name);

-- ============================================================================
-- GENERAL CONFERENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS general_conference_conferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,                 -- 2025
    month TEXT NOT NULL,                   -- "October" or "April"
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (year, month)
);

CREATE INDEX IF NOT EXISTS idx_general_conference_conferences_year
ON general_conference_conferences(year DESC, month);

CREATE TABLE IF NOT EXISTS general_conference_talks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conference_id INTEGER NOT NULL,
    speaker_name TEXT NOT NULL,            -- "Gary E. Stevenson"
    speaker_calling TEXT,                  -- "Of the Quorum of the Twelve Apostles"
    title TEXT NOT NULL,                   -- "Blessed Are the Peacemakers"
    session TEXT,                          -- "Saturday Morning Session"
    talk_id TEXT NOT NULL,                 -- "12stevenson"
    content TEXT NOT NULL,                 -- Full talk text
    url TEXT NOT NULL,
    sort_order INTEGER,                    -- Order within conference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conference_id) REFERENCES general_conference_conferences(id),
    UNIQUE (conference_id, talk_id)
);

CREATE INDEX IF NOT EXISTS idx_general_conference_talks_conference
ON general_conference_talks(conference_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_general_conference_talks_speaker
ON general_conference_talks(speaker_name);

-- ============================================================================
-- CROSS-REFERENCES (Future Feature)
-- ============================================================================

-- CREATE TABLE IF NOT EXISTS node_scripture_references (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     node_id INTEGER NOT NULL,
--     verse_id INTEGER NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
--     FOREIGN KEY (verse_id) REFERENCES scripture_verses(id),
--     UNIQUE (node_id, verse_id)
-- );
