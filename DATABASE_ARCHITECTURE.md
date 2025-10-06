# Database Architecture

This project uses two separate SQLite databases to maintain clean separation between reference data and user data.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Scripture Study Helper                     │
├─────────────────────────────────┬───────────────────────────┤
│        Mind Map Feature         │   Scripture Library       │
│                                 │                           │
│  Database: mind-map.db          │  Database:                │
│  Storage: localStorage          │    scripture-library.db   │
│  Committed: NO                  │  Storage: File (HTTP)     │
│  User Data: YES                 │  Committed: YES           │
│  Mutable: YES                   │  User Data: NO            │
│                                 │  Mutable: NO (read-only)  │
└─────────────────────────────────┴───────────────────────────┘
```

## Database Files

### 1. scripture-library.db (16 MB)

**Purpose:** Read-only reference database containing all LDS scripture content and study helps.

**Location:** `docs/scripture-library.db`

**Storage:** Loaded from file via HTTP fetch

**Committed to Git:** ✅ YES - This is reference data that all users should have

**Tables:**
- `scripture_collections` - 5 scripture collections
- `scripture_books` - 87 books
- `scripture_chapters` - 1,582 chapters with summaries
- `scripture_verses` - 41,995 verses with full text
- `topical_guide_topics` - 3,510 topics
- `topical_guide_references` - 42,477 scripture references
- `topical_guide_see_also` - Cross-references between topics
- `bible_dictionary_entries` - 1,274 encyclopedic entries

**Usage:**
```javascript
// Loaded in scripture-library.js
const response = await fetch('../scripture-library.db');
const buffer = await response.arrayBuffer();
this.db = new this.SQL.Database(new Uint8Array(buffer));
```

**Updates:**
When scripture content needs updating:
1. Run `python3 build_scripture_database.py`
2. Commit updated `docs/scripture-library.db`
3. Users get updated scripture data on next pull
4. **No conflicts** - users don't modify this database

---

### 2. mind-map.db

**Purpose:** User's personal mind map data (nodes, edges, positions).

**Location:** Browser localStorage only (not a file on disk)

**Storage:** localStorage key: `'mind-map-db'`

**Committed to Git:** ❌ NO - Each user has their own personal data

**Tables:**
- `mind_maps` - Saved mind map documents with JSON data

**Usage:**
```javascript
// Loaded in database.js
const savedDb = localStorage.getItem('mind-map-db');
const uint8Array = new Uint8Array(JSON.parse(savedDb));
this.db = new this.SQL.Database(uint8Array);
```

**Persistence:**
- Saved to localStorage on every change
- Persists across browser sessions
- Unique to each user/browser
- Can be exported/imported via UI

---

## Why Separate Databases?

### Problem with Combined Database:
```
❌ BAD: Single combined database
User creates mind maps → db changes locally
Developer updates scriptures → commits new db
User pulls updates → GIT CONFLICT! 💥
User's mind map data conflicts with scripture updates
```

### Solution with Separate Databases:
```
✅ GOOD: Separate databases
User creates mind maps → only localStorage changes
Developer updates scriptures → commits scripture-library.db
User pulls updates → scripture data updates, mind maps untouched ✓
```

## Build Process

### Scripture Database
```bash
# Build scripture database from markdown files
python3 build_scripture_database.py

# Output: docs/scripture-library.db (16 MB)
# Commit to git: YES
```

### Mind Map Database
```
# Created automatically in browser on first use
# No build process needed
# Never committed to git
```

## Deployment

### GitHub Pages Deployment
```bash
# Commit scripture database (reference data)
git add docs/scripture-library.db
git commit -m "Update scripture database"
git push

# mind-map.db is in .gitignore - never committed
# Users' mind maps stay in their browsers
```

### File Sizes
- `scripture-library.db`: ~16 MB (under GitHub's 100 MB limit ✓)
- `mind-map.db`: Varies per user (<1 MB typical)
- Total repo size impact: ~16 MB

## Future Enhancements

### Potential Cross-Linking
In the future, could add a junction table in mind-map.db:
```sql
CREATE TABLE mind_map_scripture_references (
    node_id INTEGER,
    scripture_verse_reference TEXT,  -- e.g., "Gen 1:1"
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
```

This would:
- Keep databases separate
- Allow linking mind map nodes → scripture verses
- Use text references instead of foreign keys
- Survive scripture database updates

## Summary

| Aspect | scripture-library.db | mind-map.db |
|--------|---------------------|-------------|
| Purpose | Scripture reference data | User's mind maps |
| Size | 16 MB | <1 MB |
| Storage | File (HTTP) | localStorage |
| Committed | ✅ Yes | ❌ No |
| Mutable | ❌ Read-only | ✅ Read/Write |
| Shared | ✅ All users | ❌ Per user |
| Updates | Via git pull | Via user actions |
| Technology | sql.js | sql.js |

This architecture provides:
- ✅ Clean separation of concerns
- ✅ No git conflicts on updates
- ✅ Simple deployment model
- ✅ Efficient data distribution
- ✅ User privacy (personal data stays local)
