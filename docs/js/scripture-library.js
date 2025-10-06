// Scripture Library Application

class ScriptureLibrary {
    constructor() {
        this.db = null;
        this.SQL = null;
        this.currentCollection = null;
        this.currentBook = null;
        this.currentChapter = null;
        this.allChapters = [];
        this.initialized = false;
    }

    async initialize() {
        try {
            console.log('Initializing Scripture Library...');

            // Initialize SQL.js
            await this.initializeSQLjs();

            // Load scripture database from file
            await this.loadScriptureDatabase();

            // Load initial data
            await this.loadStatistics();
            await this.loadCollections();

            // Set up event listeners
            this.setupEventListeners();

            // Hide loading screen
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('main-content').style.display = 'flex';

            this.initialized = true;
            console.log('Scripture Library initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Scripture Library:', error);
            alert('Failed to load Scripture Library. Please refresh the page.');
        }
    }

    async initializeSQLjs() {
        console.log('Initializing SQL.js...');

        // Wait for sql.js to load if needed
        let initSqlJs = window.initSqlJs;

        if (!initSqlJs) {
            console.log('Waiting for sql.js to load from CDN...');
            await new Promise((resolve, reject) => {
                let attempts = 0;
                const checkInterval = setInterval(() => {
                    if (window.initSqlJs) {
                        console.log('sql.js loaded successfully');
                        clearInterval(checkInterval);
                        resolve();
                    } else if (attempts++ > 100) {
                        clearInterval(checkInterval);
                        reject(new Error('sql.js failed to load from CDN after 10 seconds'));
                    }
                }, 100);
            });
            initSqlJs = window.initSqlJs;
        }

        this.SQL = await initSqlJs({
            locateFile: file => `https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/${file}`
        });
        console.log('SQL.js initialized');
    }

    async loadScriptureDatabase() {
        console.log('Loading scripture database...');

        try {
            // Fetch the database file from the server
            const response = await fetch('../scripture-library.db');
            if (!response.ok) {
                throw new Error(`Failed to fetch database: ${response.statusText}`);
            }

            const buffer = await response.arrayBuffer();
            const uint8Array = new Uint8Array(buffer);

            // Load the database
            this.db = new this.SQL.Database(uint8Array);
            console.log('Scripture database loaded successfully');
        } catch (error) {
            console.error('Failed to load scripture database:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Navigation selectors
        document.getElementById('collection-select').addEventListener('change', (e) => {
            this.onCollectionChange(e.target.value);
        });

        document.getElementById('book-select').addEventListener('change', (e) => {
            this.onBookChange(e.target.value);
        });

        document.getElementById('chapter-select').addEventListener('change', (e) => {
            this.onChapterChange(e.target.value);
        });

        // Search
        document.getElementById('search-btn').addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('scripture-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        document.getElementById('clear-search-btn')?.addEventListener('click', () => {
            this.clearSearch();
        });

        // Chapter navigation
        document.getElementById('prev-chapter-btn').addEventListener('click', () => {
            this.navigateChapter(-1);
        });

        document.getElementById('next-chapter-btn').addEventListener('click', () => {
            this.navigateChapter(1);
        });

        // Study helps
        document.getElementById('topical-guide-btn').addEventListener('click', () => {
            this.showTopicalGuide();
        });

        document.getElementById('bible-dict-btn').addEventListener('click', () => {
            this.showBibleDictionary();
        });

        document.getElementById('close-tg-btn')?.addEventListener('click', () => {
            this.closeStudyHelp('topical-guide-browser');
        });

        document.getElementById('close-bd-btn')?.addEventListener('click', () => {
            this.closeStudyHelp('bible-dict-browser');
        });

        // Topical Guide search
        document.getElementById('tg-search')?.addEventListener('input', (e) => {
            this.filterTopics(e.target.value);
        });

        // Bible Dictionary search
        document.getElementById('bd-search')?.addEventListener('input', (e) => {
            this.filterEntries(e.target.value);
        });
    }

    async loadStatistics() {
        try {
            // Count verses
            const verseResult = this.db.exec('SELECT COUNT(*) FROM scripture_verses');
            const verseCount = verseResult[0]?.values[0]?.[0] || 0;

            // Count chapters
            const chapterResult = this.db.exec('SELECT COUNT(*) FROM scripture_chapters');
            const chapterCount = chapterResult[0]?.values[0]?.[0] || 0;

            // Count books
            const bookResult = this.db.exec('SELECT COUNT(*) FROM scripture_books');
            const bookCount = bookResult[0]?.values[0]?.[0] || 0;

            // Update UI
            document.getElementById('stat-verses').textContent = verseCount.toLocaleString();
            document.getElementById('stat-chapters').textContent = chapterCount.toLocaleString();
            document.getElementById('stat-books').textContent = bookCount.toLocaleString();
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    async loadCollections() {
        try {
            const result = this.db.exec(`
                SELECT id, name, abbreviation
                FROM scripture_collections
                ORDER BY sort_order
            `);

            if (result.length === 0) return;

            const select = document.getElementById('collection-select');
            select.innerHTML = '<option value="">Select a collection...</option>';

            result[0].values.forEach(([id, name, abbr]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load collections:', error);
        }
    }

    async onCollectionChange(collectionId) {
        if (!collectionId) {
            document.getElementById('book-select').disabled = true;
            document.getElementById('chapter-select').disabled = true;
            return;
        }

        this.currentCollection = collectionId;
        await this.loadBooks(collectionId);
    }

    async loadBooks(collectionId) {
        try {
            const result = this.db.exec(`
                SELECT id, name
                FROM scripture_books
                WHERE collection_id = ?
                ORDER BY sort_order
            `, [parseInt(collectionId)]);

            const select = document.getElementById('book-select');
            select.innerHTML = '<option value="">Select a book...</option>';

            if (result.length > 0) {
                result[0].values.forEach(([id, name]) => {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = name;
                    select.appendChild(option);
                });
            }

            select.disabled = false;
            document.getElementById('chapter-select').disabled = true;
        } catch (error) {
            console.error('Failed to load books:', error);
        }
    }

    async onBookChange(bookId) {
        if (!bookId) {
            document.getElementById('chapter-select').disabled = true;
            return;
        }

        this.currentBook = bookId;
        await this.loadChapters(bookId);
    }

    async loadChapters(bookId) {
        try {
            const result = this.db.exec(`
                SELECT id, chapter_number, title
                FROM scripture_chapters
                WHERE book_id = ?
                ORDER BY chapter_number
            `, [parseInt(bookId)]);

            const select = document.getElementById('chapter-select');
            select.innerHTML = '<option value="">Select a chapter...</option>';

            if (result.length > 0) {
                this.allChapters = result[0].values;
                result[0].values.forEach(([id, number, title]) => {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = `Chapter ${number}`;
                    select.appendChild(option);
                });
            }

            select.disabled = false;
        } catch (error) {
            console.error('Failed to load chapters:', error);
        }
    }

    async onChapterChange(chapterId) {
        if (!chapterId) return;

        this.currentChapter = parseInt(chapterId);
        await this.displayChapter(this.currentChapter);
    }

    async displayChapter(chapterId) {
        try {
            // Get chapter info
            const chapterResult = this.db.exec(`
                SELECT
                    ch.chapter_number,
                    ch.title,
                    ch.summary,
                    b.name as book_name,
                    c.name as collection_name
                FROM scripture_chapters ch
                JOIN scripture_books b ON b.id = ch.book_id
                JOIN scripture_collections c ON c.id = b.collection_id
                WHERE ch.id = ?
            `, [chapterId]);

            if (chapterResult.length === 0) return;

            const [chapterNum, title, summary, bookName, collectionName] = chapterResult[0].values[0];

            // Get verses
            const versesResult = this.db.exec(`
                SELECT verse_number, text
                FROM scripture_verses
                WHERE chapter_id = ?
                ORDER BY verse_number
            `, [chapterId]);

            // Hide other views
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('search-results').style.display = 'none';
            document.getElementById('topical-guide-browser').style.display = 'none';
            document.getElementById('bible-dict-browser').style.display = 'none';

            // Show chapter reader
            const reader = document.getElementById('chapter-reader');
            reader.style.display = 'block';

            // Update header
            document.getElementById('chapter-title').textContent = title || bookName;
            document.getElementById('chapter-reference').textContent =
                `${collectionName} - ${bookName} ${chapterNum}`;

            // Update summary
            const summaryEl = document.getElementById('chapter-summary');
            if (summary && summary.trim()) {
                summaryEl.textContent = summary;
                summaryEl.style.display = 'block';
            } else {
                summaryEl.style.display = 'none';
            }

            // Display verses
            const versesContainer = document.getElementById('chapter-verses');
            versesContainer.innerHTML = '';

            if (versesResult.length > 0) {
                versesResult[0].values.forEach(([verseNum, text]) => {
                    const verseDiv = document.createElement('div');
                    verseDiv.className = 'verse';
                    verseDiv.innerHTML = `
                        <span class="verse-number">${verseNum}</span>
                        <span class="verse-text">${text}</span>
                    `;
                    versesContainer.appendChild(verseDiv);
                });
            }

            // Update navigation buttons
            this.updateChapterNavigation();

            // Scroll to top
            reader.scrollTop = 0;
        } catch (error) {
            console.error('Failed to display chapter:', error);
        }
    }

    updateChapterNavigation() {
        const currentIndex = this.allChapters.findIndex(ch => ch[0] === this.currentChapter);

        const prevBtn = document.getElementById('prev-chapter-btn');
        const nextBtn = document.getElementById('next-chapter-btn');

        prevBtn.disabled = currentIndex <= 0;
        nextBtn.disabled = currentIndex >= this.allChapters.length - 1;
    }

    navigateChapter(direction) {
        const currentIndex = this.allChapters.findIndex(ch => ch[0] === this.currentChapter);
        const newIndex = currentIndex + direction;

        if (newIndex >= 0 && newIndex < this.allChapters.length) {
            const newChapterId = this.allChapters[newIndex][0];
            document.getElementById('chapter-select').value = newChapterId;
            this.displayChapter(newChapterId);
            this.currentChapter = newChapterId;
        }
    }

    async performSearch() {
        const query = document.getElementById('scripture-search').value.trim();
        if (!query) return;

        try {
            // Search verses (using LIKE since FTS5 not available)
            const result = this.db.exec(`
                SELECT
                    v.id,
                    v.verse_number,
                    v.text,
                    ch.chapter_number,
                    b.name as book_name,
                    c.name as collection_name,
                    ch.id as chapter_id
                FROM scripture_verses v
                JOIN scripture_chapters ch ON ch.id = v.chapter_id
                JOIN scripture_books b ON b.id = ch.book_id
                JOIN scripture_collections c ON c.id = b.collection_id
                WHERE v.text LIKE ?
                ORDER BY c.sort_order, b.sort_order, ch.chapter_number, v.verse_number
                LIMIT 100
            `, [`%${query}%`]);

            // Hide other views
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('chapter-reader').style.display = 'none';
            document.getElementById('topical-guide-browser').style.display = 'none';
            document.getElementById('bible-dict-browser').style.display = 'none';

            // Show search results
            const resultsContainer = document.getElementById('results-list');
            resultsContainer.innerHTML = '';

            if (result.length === 0 || result[0].values.length === 0) {
                resultsContainer.innerHTML = '<p>No results found.</p>';
            } else {
                result[0].values.forEach(([id, verseNum, text, chapterNum, bookName, collectionName, chapterId]) => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'search-result-item';
                    resultDiv.innerHTML = `
                        <div class="result-reference">${bookName} ${chapterNum}:${verseNum}</div>
                        <div class="result-text">${this.highlightText(text, query)}</div>
                    `;
                    resultDiv.addEventListener('click', () => {
                        this.displayChapter(chapterId);
                    });
                    resultsContainer.appendChild(resultDiv);
                });
            }

            document.getElementById('search-results').style.display = 'block';
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    highlightText(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    clearSearch() {
        document.getElementById('scripture-search').value = '';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('welcome-screen').style.display = 'flex';
    }

    async showTopicalGuide() {
        try {
            const result = this.db.exec(`
                SELECT id, topic_name
                FROM topical_guide_topics
                ORDER BY topic_name
            `);

            // Hide other views
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('chapter-reader').style.display = 'none';
            document.getElementById('search-results').style.display = 'none';
            document.getElementById('bible-dict-browser').style.display = 'none';

            // Display topics
            const topicsList = document.getElementById('tg-topics-list');
            topicsList.innerHTML = '';
            topicsList.style.display = 'grid';
            document.getElementById('tg-topic-detail').style.display = 'none';

            if (result.length > 0) {
                result[0].values.slice(0, 100).forEach(([id, name]) => {
                    const topicDiv = document.createElement('div');
                    topicDiv.className = 'topic-item';
                    topicDiv.textContent = name;
                    topicDiv.addEventListener('click', () => {
                        this.showTopicDetail(id, name);
                    });
                    topicsList.appendChild(topicDiv);
                });
            }

            document.getElementById('topical-guide-browser').style.display = 'block';
        } catch (error) {
            console.error('Failed to load Topical Guide:', error);
        }
    }

    async showTopicDetail(topicId, topicName) {
        try {
            // Get references
            const result = this.db.exec(`
                SELECT collection_name, scripture_text, citation
                FROM topical_guide_references
                WHERE topic_id = ?
                ORDER BY sort_order
            `, [topicId]);

            const detailDiv = document.getElementById('tg-topic-detail');
            detailDiv.innerHTML = `<h3>${topicName}</h3>`;

            if (result.length > 0 && result[0].values.length > 0) {
                const refsByCollection = {};
                result[0].values.forEach(([collection, text, citation]) => {
                    if (!refsByCollection[collection]) {
                        refsByCollection[collection] = [];
                    }
                    refsByCollection[collection].push({ text, citation });
                });

                for (const [collection, refs] of Object.entries(refsByCollection)) {
                    const sectionDiv = document.createElement('div');
                    sectionDiv.innerHTML = `<h4>${collection}</h4>`;
                    refs.forEach(({ text, citation }) => {
                        const refDiv = document.createElement('div');
                        refDiv.className = 'scripture-reference';
                        refDiv.innerHTML = `
                            <span class="reference-citation">${citation}</span> - ${text}
                        `;
                        sectionDiv.appendChild(refDiv);
                    });
                    detailDiv.appendChild(sectionDiv);
                }
            }

            document.getElementById('tg-topics-list').style.display = 'none';
            detailDiv.style.display = 'block';
        } catch (error) {
            console.error('Failed to load topic detail:', error);
        }
    }

    async showBibleDictionary() {
        try {
            const result = this.db.exec(`
                SELECT id, entry_name
                FROM bible_dictionary_entries
                ORDER BY entry_name
            `);

            // Hide other views
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('chapter-reader').style.display = 'none';
            document.getElementById('search-results').style.display = 'none';
            document.getElementById('topical-guide-browser').style.display = 'none';

            // Display entries
            const entriesList = document.getElementById('bd-entries-list');
            entriesList.innerHTML = '';
            entriesList.style.display = 'grid';
            document.getElementById('bd-entry-detail').style.display = 'none';

            if (result.length > 0) {
                result[0].values.slice(0, 100).forEach(([id, name]) => {
                    const entryDiv = document.createElement('div');
                    entryDiv.className = 'entry-item';
                    entryDiv.textContent = name;
                    entryDiv.addEventListener('click', () => {
                        this.showEntryDetail(id, name);
                    });
                    entriesList.appendChild(entryDiv);
                });
            }

            document.getElementById('bible-dict-browser').style.display = 'block';
        } catch (error) {
            console.error('Failed to load Bible Dictionary:', error);
        }
    }

    async showEntryDetail(entryId, entryName) {
        try {
            const result = this.db.exec(`
                SELECT body
                FROM bible_dictionary_entries
                WHERE id = ?
            `, [entryId]);

            const detailDiv = document.getElementById('bd-entry-detail');

            if (result.length > 0 && result[0].values.length > 0) {
                const body = result[0].values[0][0];
                detailDiv.innerHTML = `
                    <h3>${entryName}</h3>
                    <div>${body.replace(/\n/g, '<br>')}</div>
                `;
            }

            document.getElementById('bd-entries-list').style.display = 'none';
            detailDiv.style.display = 'block';
        } catch (error) {
            console.error('Failed to load entry detail:', error);
        }
    }

    closeStudyHelp(browserId) {
        document.getElementById(browserId).style.display = 'none';
        document.getElementById('welcome-screen').style.display = 'flex';
    }

    filterTopics(query) {
        // Simple client-side filtering
        const items = document.querySelectorAll('.topic-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(query.toLowerCase()) ? 'block' : 'none';
        });
    }

    filterEntries(query) {
        // Simple client-side filtering
        const items = document.querySelectorAll('.entry-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(query.toLowerCase()) ? 'block' : 'none';
        });
    }
}

// Initialize when page loads
const scriptureLibrary = new ScriptureLibrary();
window.addEventListener('DOMContentLoaded', () => {
    scriptureLibrary.initialize();
});
