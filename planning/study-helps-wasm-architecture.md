# Study Helps WASM Architecture Plan - From First Principles

## Understanding the Existing WASM Architecture

### Mind Map (✅ Works Locally)

**Architecture:**
```
User opens mind-map.html
    ↓
Load SQL.js WASM library
    ↓
Create EMPTY SQLite database in memory
    ↓
User creates nodes/edges through UI
    ↓
Data exists only in browser memory
    ↓
Export database to Uint8Array
    ↓
Save to localStorage as JSON
    ↓
On reload: Load from localStorage → Recreate database
```

**Key Insight:** No files fetched. Data is CREATED in browser, then persisted to localStorage.

**Why it works locally:**
- ✅ No `fetch()` calls
- ✅ Uses localStorage (browser API, always available)
- ✅ Self-contained

### Scripture Library (❌ Fails Locally)

**Architecture:**
```
User opens scripture-library.html
    ↓
Load SQL.js WASM library
    ↓
fetch('../scripture-library.db')  ← BLOCKED with file://
    ↓
Load database file into memory
    ↓
Query database
```

**Why it fails locally:**
- ❌ Uses `fetch()` which is blocked on file:// protocol
- ❌ Requires web server or GitHub Pages

**File size:** 16 MB (41,995 verses, 5 collections, 87 books, 1,582 chapters)

## The Core Problem

**For Study Helps to work locally, we cannot use `fetch()`.**

We need data to be available WITHOUT fetching a file.

## Solution Space Analysis

### What Data Do We Need?

**Topical Guide:**
- 3,510 topics
- 42,477 scripture references
- Each reference has: excerpt, citation, collection, book, reference

**Bible Dictionary:**
- 1,274 entries
- Each entry has: name, body text (encyclopedic content)

**Estimated Data Size:**
- Topical Guide: ~3-5 MB as JSON
- Bible Dictionary: ~2-3 MB as JSON
- **Total: ~5-8 MB**

### Constraint: Must Work Locally Without Server

Options that work with file:// protocol:
1. ✅ JavaScript source files
2. ✅ localStorage
3. ✅ IndexedDB
4. ❌ fetch() - blocked
5. ❌ XMLHttpRequest - blocked

## The WASM-Consistent Solution

### Core Idea: Pre-Generate JavaScript Data Files

**Just like Mind Map creates data in the browser, we'll "pre-create" the data as JavaScript source code.**

**Build Process:**
```
Python script reads database
    ↓
Exports data as JavaScript objects
    ↓
Generates topical-guide-data.js
    ↓
Generates bible-dictionary-data.js
```

**Runtime Process:**
```
User opens topical-guide.html
    ↓
Load SQL.js WASM library
    ↓
Load topical-guide-data.js (JavaScript file, no fetch)
    ↓
Create EMPTY SQLite database in memory
    ↓
Populate database from JavaScript data
    ↓
Query database normally with SQL
```

**This is identical to Mind Map's pattern, except:**
- Mind Map: User populates data through UI
- Study Helps: JavaScript code populates data automatically

## Architecture Diagram

```
┌─────────────────────────────────────┐
│     Existing Data Sources           │
├─────────────────────────────────────┤
│  study_helps/topical_guide/*.md     │
│  study_helps/bible_dictionary/*.md  │
│  docs/scripture-library.db          │
└─────────────────────────────────────┘
            │
            ↓ (NEW BUILD STEP)
┌─────────────────────────────────────┐
│   Python Export Scripts             │
├─────────────────────────────────────┤
│  export_topical_guide_data.py       │
│  export_bible_dictionary_data.py    │
└─────────────────────────────────────┘
            │
            ↓ (GENERATES)
┌─────────────────────────────────────┐
│   JavaScript Data Files             │
├─────────────────────────────────────┤
│  docs/js/topical-guide-data.js      │
│  docs/js/bible-dictionary-data.js   │
│                                     │
│  const TOPICAL_GUIDE = {            │
│    topics: [{id, name}, ...],       │
│    references: [{...}, ...]         │
│  };                                 │
└─────────────────────────────────────┘
            │
            ↓ (LOADED BY)
┌─────────────────────────────────────┐
│         HTML Pages                  │
├─────────────────────────────────────┤
│  topical-guide.html                 │
│  <script src="data.js"></script>    │
│  <script src="app.js"></script>     │
└─────────────────────────────────────┘
            │
            ↓ (EXECUTES)
┌─────────────────────────────────────┐
│    Application JavaScript           │
├─────────────────────────────────────┤
│  1. Load SQL.js WASM                │
│  2. Create empty DB in memory       │
│  3. Run CREATE TABLE statements     │
│  4. INSERT data from JS objects     │
│  5. Query with SQL as normal        │
└─────────────────────────────────────┘
            │
            ↓
┌─────────────────────────────────────┐
│    SQLite Database (in memory)      │
│    Same as Mind Map pattern!        │
└─────────────────────────────────────┘
```

## Implementation Details

### 1. Build Scripts (Python)

**File:** `build_topical_guide_data.py`

```python
#!/usr/bin/env python3
"""
Export Topical Guide data from database to JavaScript.
Generates docs/js/topical-guide-data.js
"""

import sqlite3
import json

def export_topical_guide():
    db = sqlite3.connect('docs/scripture-library.db')
    cursor = db.cursor()

    # Get all topics
    topics = cursor.execute("""
        SELECT id, topic_name
        FROM topical_guide_topics
        ORDER BY topic_name
    """).fetchall()

    # Get all references
    references = cursor.execute("""
        SELECT topic_id, excerpt_text, citation, collection, book, reference
        FROM topical_guide_references
        ORDER BY topic_id, collection, book, reference
    """).fetchall()

    # Convert to JavaScript format
    data = {
        'topics': [
            {'id': t[0], 'name': t[1]}
            for t in topics
        ],
        'references': [
            {
                'topicId': r[0],
                'excerpt': r[1],
                'citation': r[2],
                'collection': r[3],
                'book': r[4],
                'reference': r[5]
            }
            for r in references
        ]
    }

    # Generate JavaScript file
    js_code = f"""/**
 * Topical Guide Data
 * Auto-generated from scripture-library.db
 * DO NOT EDIT MANUALLY - Run build_topical_guide_data.py to regenerate
 *
 * Contains:
 * - {len(data['topics'])} topics
 * - {len(data['references'])} scripture references
 */

const TOPICAL_GUIDE_DATA = {json.dumps(data, indent=2)};
"""

    # Write to file
    with open('docs/js/topical-guide-data.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    print(f"✅ Generated topical-guide-data.js")
    print(f"   Topics: {len(data['topics'])}")
    print(f"   References: {len(data['references'])}")

    db.close()

if __name__ == '__main__':
    export_topical_guide()
```

**File:** `build_bible_dictionary_data.py`

```python
#!/usr/bin/env python3
"""
Export Bible Dictionary data from database to JavaScript.
Generates docs/js/bible-dictionary-data.js
"""

import sqlite3
import json

def export_bible_dictionary():
    db = sqlite3.connect('docs/scripture-library.db')
    cursor = db.cursor()

    # Get all entries
    entries = cursor.execute("""
        SELECT id, entry_name, body_text
        FROM bible_dictionary_entries
        ORDER BY entry_name
    """).fetchall()

    # Convert to JavaScript format
    data = {
        'entries': [
            {
                'id': e[0],
                'name': e[1],
                'body': e[2]
            }
            for e in entries
        ]
    }

    # Generate JavaScript file
    js_code = f"""/**
 * Bible Dictionary Data
 * Auto-generated from scripture-library.db
 * DO NOT EDIT MANUALLY - Run build_bible_dictionary_data.py to regenerate
 *
 * Contains:
 * - {len(data['entries'])} dictionary entries
 */

const BIBLE_DICTIONARY_DATA = {json.dumps(data, indent=2)};
"""

    # Write to file
    with open('docs/js/bible-dictionary-data.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    print(f"✅ Generated bible-dictionary-data.js")
    print(f"   Entries: {len(data['entries'])}")

    db.close()

if __name__ == '__main__':
    export_bible_dictionary()
```

### 2. HTML Pages

**File:** `docs/pages/topical-guide.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Topical Guide - Scripture Study Helper</title>
    <link rel="stylesheet" href="../css/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/sql-wasm.js"></script>
</head>
<body>
    <header id="app-header">
        <!-- Navigation -->
    </header>

    <main class="topical-guide-page">
        <div id="loading-indicator">Loading Topical Guide...</div>
        <div id="content" style="display: none;">
            <!-- UI elements -->
        </div>
    </main>

    <!-- Load data BEFORE app logic -->
    <script src="../js/topical-guide-data.js"></script>
    <script src="../js/topical-guide.js"></script>
</body>
</html>
```

### 3. Application JavaScript

**File:** `docs/js/topical-guide.js`

```javascript
class TopicalGuideBrowser {
    constructor() {
        this.db = null;
        this.SQL = null;
        this.allTopics = [];
    }

    async initialize() {
        console.log('Initializing Topical Guide...');

        // Step 1: Initialize SQL.js WASM
        await this.initializeSQLjs();

        // Step 2: Create empty database in memory
        this.db = new this.SQL.Database();

        // Step 3: Create schema
        this.createSchema();

        // Step 4: Populate from JavaScript data
        this.populateDatabase();

        // Step 5: Load topics for UI
        this.loadTopics();

        // Hide loading, show content
        document.getElementById('loading-indicator').style.display = 'none';
        document.getElementById('content').style.display = 'block';

        console.log('Topical Guide initialized successfully');
    }

    async initializeSQLjs() {
        let initSqlJs = window.initSqlJs;
        if (!initSqlJs) {
            await new Promise((resolve, reject) => {
                let attempts = 0;
                const checkInterval = setInterval(() => {
                    if (window.initSqlJs) {
                        clearInterval(checkInterval);
                        resolve();
                    } else if (attempts++ > 100) {
                        clearInterval(checkInterval);
                        reject(new Error('SQL.js failed to load'));
                    }
                }, 100);
            });
            initSqlJs = window.initSqlJs;
        }

        this.SQL = await initSqlJs({
            locateFile: file => `https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/${file}`
        });
    }

    createSchema() {
        // Create tables
        this.db.run(`
            CREATE TABLE topics (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        `);

        this.db.run(`
            CREATE TABLE references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                excerpt TEXT,
                citation TEXT,
                collection TEXT,
                book TEXT,
                reference TEXT
            )
        `);

        // Create index for faster lookups
        this.db.run(`CREATE INDEX idx_topic_id ON references(topic_id)`);
    }

    populateDatabase() {
        console.log('Populating database from JavaScript data...');

        // Insert topics
        const insertTopic = this.db.prepare('INSERT INTO topics (id, name) VALUES (?, ?)');
        TOPICAL_GUIDE_DATA.topics.forEach(topic => {
            insertTopic.run([topic.id, topic.name]);
        });
        insertTopic.free();

        // Insert references
        const insertRef = this.db.prepare(`
            INSERT INTO references (topic_id, excerpt, citation, collection, book, reference)
            VALUES (?, ?, ?, ?, ?, ?)
        `);
        TOPICAL_GUIDE_DATA.references.forEach(ref => {
            insertRef.run([
                ref.topicId,
                ref.excerpt,
                ref.citation,
                ref.collection,
                ref.book,
                ref.reference
            ]);
        });
        insertRef.free();

        console.log(`Loaded ${TOPICAL_GUIDE_DATA.topics.length} topics and ${TOPICAL_GUIDE_DATA.references.length} references`);
    }

    loadTopics() {
        const result = this.db.exec('SELECT id, name FROM topics ORDER BY name');
        if (result.length > 0) {
            this.allTopics = result[0].values.map(row => ({
                id: row[0],
                name: row[1]
            }));
        }
        this.displayTopics();
    }

    displayTopics() {
        // Same UI rendering logic as before
        // ...
    }

    async loadTopicReferences(topicId) {
        const result = this.db.exec(`
            SELECT excerpt, citation, collection, book, reference
            FROM references
            WHERE topic_id = ?
            ORDER BY collection, book, reference
        `, [topicId]);

        // Same rendering logic as before
        // ...
    }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new TopicalGuideBrowser();
    app.initialize();
});
```

## Advantages of This Approach

### ✅ Consistent with WASM Architecture
- Uses SQL.js WASM (same as Mind Map)
- Creates database in memory
- No external file dependencies
- Pure client-side

### ✅ Works Locally Without Server
- JavaScript files are part of the HTML page
- No `fetch()` calls
- No CORS issues
- Opens with file:// protocol

### ✅ Works on GitHub Pages
- Same code works online and offline
- No special configuration
- Fast loading (static files)

### ✅ Maintainable
- Data generation is automated (Python scripts)
- Source of truth is still the database
- Easy to regenerate when data changes

### ✅ Performance
- Initial load: Parse JavaScript (~5-8 MB)
- Database creation: Fast (happens in memory)
- Subsequent queries: Full SQLite performance
- No network requests after page load

## File Size Analysis

**Topical Guide Data:**
- 3,510 topics × ~30 bytes = ~105 KB
- 42,477 references × ~150 bytes = ~6.4 MB
- **Total: ~6.5 MB JavaScript**

**Bible Dictionary Data:**
- 1,274 entries × ~2KB average = ~2.5 MB
- **Total: ~2.5 MB JavaScript**

**Combined: ~9 MB of JavaScript data files**

**Is this acceptable?**
- ✅ Modern browsers handle 10+ MB JavaScript easily
- ✅ Files are loaded once, then cached
- ✅ Minification could reduce size further
- ✅ Gzip compression by web servers reduces transfer size
- ✅ Much smaller than video/image files on typical websites

## Build Process

```bash
# Generate data files from database
python3 build_topical_guide_data.py
python3 build_bible_dictionary_data.py

# Outputs:
# docs/js/topical-guide-data.js
# docs/js/bible-dictionary-data.js

# These files are committed to git and deployed
git add docs/js/topical-guide-data.js
git add docs/js/bible-dictionary-data.js
git commit -m "Generate Study Helps data files"
git push
```

## Comparison to Scripture Library

**Scripture Library:**
- 41,995 verses × ~200 bytes = ~8.4 MB
- Plus book/chapter structure
- **Total: ~16 MB database file**
- Too large to convert to JavaScript (40+ MB as JSON)
- **Decision: Keep as-is, GitHub Pages only**

**Study Helps:**
- Smaller datasets (9 MB total)
- Feasible as JavaScript
- **Decision: Convert to JavaScript, works everywhere**

## Implementation Plan

### Phase 1: Build Scripts
- [ ] Create `build_topical_guide_data.py`
- [ ] Create `build_bible_dictionary_data.py`
- [ ] Test generation from database
- [ ] Verify file sizes

### Phase 2: Topical Guide
- [ ] Create `docs/pages/topical-guide.html`
- [ ] Create `docs/js/topical-guide.js`
- [ ] Implement database creation from data
- [ ] Implement UI and search
- [ ] Test locally with file://
- [ ] Test on GitHub Pages

### Phase 3: Bible Dictionary
- [ ] Create `docs/pages/bible-dictionary.html`
- [ ] Create `docs/js/bible-dictionary.js`
- [ ] Implement database creation from data
- [ ] Implement UI and search
- [ ] Test locally with file://
- [ ] Test on GitHub Pages

### Phase 4: Integration
- [ ] Create Study Helps landing page
- [ ] Update home page navigation
- [ ] Add CSS styling
- [ ] Documentation
- [ ] Final testing

## Success Criteria

✅ Topical Guide works with file:// protocol
✅ Bible Dictionary works with file:// protocol
✅ Both work on GitHub Pages
✅ Same codebase for both environments
✅ No server required
✅ Full SQL query capabilities
✅ Fast performance
✅ Uses SQL.js WASM (consistent architecture)

## This IS the WASM Architecture

**Mind Map pattern:**
```
Empty DB → User populates → Export → localStorage
```

**Study Helps pattern:**
```
Empty DB → JavaScript populates → Query → Display
```

**Same architecture, different data source:**
- Mind Map: User creates data
- Study Helps: Build script creates data

Both use SQL.js WASM to create SQLite databases in memory. Both work locally. Both are pure client-side. Perfect consistency.
