-- Follow Him Database Schema
-- Separate database for Follow Him podcast content

-- ============================================================================
-- FOLLOW HIM PODCAST
-- ============================================================================

CREATE TABLE IF NOT EXISTS followhim_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "Doctrine and Covenants 2025"
    year INTEGER NOT NULL,                 -- 2025
    scripture_focus TEXT,                  -- "Doctrine and Covenants"
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS idx_followhim_series_year
ON followhim_series(year DESC);

CREATE TABLE IF NOT EXISTS followhim_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,       -- 1, 2, 3...
    title TEXT NOT NULL,                   -- "The Restoration of the Gospel of Jesus Christ"
    scripture_reference TEXT,              -- "D&C 1" or "Joseph Smith History 1:1-26"
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES followhim_series(id),
    UNIQUE (series_id, episode_number)
);

CREATE INDEX IF NOT EXISTS idx_followhim_episodes_series
ON followhim_episodes(series_id, sort_order);

CREATE TABLE IF NOT EXISTS followhim_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL,
    part_type TEXT NOT NULL,               -- "Part 1", "Part 2", "Favorites"
    title TEXT NOT NULL,                   -- Full title from page
    guest TEXT,                            -- "Dr. Tyler Griffin"
    content TEXT NOT NULL,                 -- Full transcript
    url TEXT NOT NULL,
    sort_order INTEGER NOT NULL,           -- 1, 2, 3 for Part 1, Part 2, Favorites
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES followhim_episodes(id),
    UNIQUE (episode_id, part_type)
);

CREATE INDEX IF NOT EXISTS idx_followhim_parts_episode
ON followhim_parts(episode_id, sort_order);
