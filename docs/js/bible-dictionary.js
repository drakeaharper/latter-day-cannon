// Bible Dictionary Browser
// Uses scripture-library.db (same database as Scripture Library)

class BibleDictionaryBrowser {
    constructor() {
        this.db = null;
        this.SQL = null;
        this.allEntries = [];
        this.filteredEntries = [];
        this.currentLetter = null;
        this.expandedEntries = new Set();
        this.initialized = false;
    }

    async initialize() {
        try {
            console.log('Initializing Bible Dictionary...');

            // Initialize SQL.js
            await this.initializeSQLjs();

            // Load scripture database (same as Scripture Library)
            await this.loadScriptureDatabase();

            // Load all entries
            await this.loadAllEntries();

            // Set up UI
            this.setupAlphabeticalNav();
            this.setupSearchListener();

            // Display all entries initially
            this.displayEntries(this.allEntries);

            // Hide loading screen
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';

            this.initialized = true;
            console.log('Bible Dictionary initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Bible Dictionary:', error);
            document.getElementById('loading-screen').innerHTML =
                `<p style="color: var(--danger-color); text-align: center; padding: 2rem;">
                    Failed to load Bible Dictionary. Please refresh the page.<br>
                    <small>Error: ${error.message}</small>
                </p>`;
        }
    }

    async initializeSQLjs() {
        console.log('Initializing SQL.js...');

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
            // Fetch the database file (same as Scripture Library)
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

    async loadAllEntries() {
        console.log('Loading all dictionary entries...');

        try {
            const result = this.db.exec(`
                SELECT id, entry_name
                FROM bible_dictionary_entries
                ORDER BY entry_name
            `);

            if (result.length === 0 || !result[0].values) {
                this.allEntries = [];
                return;
            }

            this.allEntries = result[0].values.map(row => ({
                id: row[0],
                name: row[1]
            }));

            this.filteredEntries = [...this.allEntries];

            // Update count in header
            document.getElementById('entry-count').textContent = this.allEntries.length.toLocaleString();

            console.log(`Loaded ${this.allEntries.length} entries`);
        } catch (error) {
            console.error('Failed to load entries:', error);
            throw error;
        }
    }

    setupAlphabeticalNav() {
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        const navContainer = document.getElementById('alphabet-nav');

        alphabet.forEach(letter => {
            const btn = document.createElement('button');
            btn.className = 'alphabet-btn';
            btn.textContent = letter;
            btn.addEventListener('click', () => this.filterByLetter(letter));
            navContainer.appendChild(btn);
        });

        // Show all button
        document.getElementById('show-all-btn').addEventListener('click', () => {
            this.showAll();
        });
    }

    setupSearchListener() {
        const searchInput = document.getElementById('entry-search');

        searchInput.addEventListener('input', (e) => {
            this.searchEntries(e.target.value);
        });
    }

    searchEntries(query) {
        const searchTerm = query.toLowerCase().trim();

        if (searchTerm === '') {
            this.filteredEntries = [...this.allEntries];
        } else {
            this.filteredEntries = this.allEntries.filter(entry =>
                entry.name.toLowerCase().includes(searchTerm)
            );
        }

        this.currentLetter = null;
        this.updateAlphabetButtons();
        this.displayEntries(this.filteredEntries);
        this.updateResultsCount();
    }

    filterByLetter(letter) {
        this.currentLetter = letter;
        this.filteredEntries = this.allEntries.filter(entry =>
            entry.name.toUpperCase().startsWith(letter)
        );

        this.updateAlphabetButtons();
        this.displayEntries(this.filteredEntries);
        this.updateResultsCount();

        // Clear search input
        document.getElementById('entry-search').value = '';
    }

    showAll() {
        this.currentLetter = null;
        this.filteredEntries = [...this.allEntries];

        this.updateAlphabetButtons();
        this.displayEntries(this.filteredEntries);
        this.updateResultsCount();

        // Clear search input
        document.getElementById('entry-search').value = '';
    }

    updateAlphabetButtons() {
        const buttons = document.querySelectorAll('.alphabet-btn');
        buttons.forEach(btn => {
            if (btn.textContent === this.currentLetter) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    displayEntries(entries) {
        const container = document.getElementById('entry-list');
        const noResults = document.getElementById('no-results');

        if (entries.length === 0) {
            container.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }

        noResults.style.display = 'none';
        container.innerHTML = '';

        entries.forEach(entry => {
            const entryDiv = document.createElement('div');
            entryDiv.className = 'entry-item';
            entryDiv.dataset.entryId = entry.id;

            const header = document.createElement('div');
            header.className = 'entry-header';
            header.innerHTML = `
                <h3 class="entry-title">${this.escapeHtml(entry.name)}</h3>
                <button class="expand-btn" aria-label="Expand entry">+</button>
            `;

            const content = document.createElement('div');
            content.className = 'entry-content';
            content.style.display = 'none';
            content.innerHTML = '<div class="loading-entry">Loading entry...</div>';

            header.addEventListener('click', () => {
                this.toggleEntry(entry.id, entryDiv, content);
            });

            entryDiv.appendChild(header);
            entryDiv.appendChild(content);
            container.appendChild(entryDiv);
        });
    }

    async toggleEntry(entryId, entryDiv, contentDiv) {
        if (this.expandedEntries.has(entryId)) {
            // Collapse
            this.expandedEntries.delete(entryId);
            contentDiv.style.display = 'none';
            entryDiv.querySelector('.expand-btn').textContent = '+';
            entryDiv.classList.remove('expanded');
        } else {
            // Expand
            this.expandedEntries.add(entryId);
            contentDiv.style.display = 'block';
            entryDiv.querySelector('.expand-btn').textContent = '−';
            entryDiv.classList.add('expanded');

            // Load entry content if not already loaded
            if (contentDiv.querySelector('.loading-entry')) {
                await this.loadEntryContent(entryId, contentDiv);
            }
        }
    }

    async loadEntryContent(entryId, contentDiv) {
        try {
            const result = this.db.exec(`
                SELECT entry_name, body_text
                FROM bible_dictionary_entries
                WHERE id = ?
            `, [entryId]);

            if (result.length === 0 || !result[0].values || result[0].values.length === 0) {
                contentDiv.innerHTML = '<p class="no-content">No content found for this entry.</p>';
                return;
            }

            const [entryName, bodyText] = result[0].values[0];

            // Format body text with paragraphs preserved
            const formattedText = this.formatBodyText(bodyText);

            contentDiv.innerHTML = `<div class="entry-body">${formattedText}</div>`;
        } catch (error) {
            console.error('Failed to load entry content:', error);
            contentDiv.innerHTML = '<p class="error">Failed to load entry content.</p>';
        }
    }

    formatBodyText(text) {
        if (!text) return '<p>No content available.</p>';

        // Split by double newlines to preserve paragraphs
        const paragraphs = text.split('\n\n')
            .map(p => p.trim())
            .filter(p => p.length > 0);

        return paragraphs
            .map(p => `<p>${this.escapeHtml(p)}</p>`)
            .join('');
    }

    updateResultsCount() {
        const count = this.filteredEntries.length;
        const countDiv = document.getElementById('search-results-count');

        if (count === this.allEntries.length) {
            countDiv.textContent = `Showing all ${count.toLocaleString()} entries`;
        } else {
            countDiv.textContent = `Showing ${count.toLocaleString()} of ${this.allEntries.length.toLocaleString()} entries`;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const browser = new BibleDictionaryBrowser();
    await browser.initialize();
});
