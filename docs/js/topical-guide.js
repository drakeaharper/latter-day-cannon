// Topical Guide Browser
// Uses scripture-library.db (same database as Scripture Library)

class TopicalGuideBrowser {
    constructor() {
        this.db = null;
        this.SQL = null;
        this.allTopics = [];
        this.filteredTopics = [];
        this.currentLetter = null;
        this.expandedTopics = new Set();
        this.initialized = false;
    }

    async initialize() {
        try {
            console.log('Initializing Topical Guide...');

            // Initialize SQL.js
            await this.initializeSQLjs();

            // Load scripture database (same as Scripture Library)
            await this.loadScriptureDatabase();

            // Load all topics
            await this.loadAllTopics();

            // Set up UI
            this.setupAlphabeticalNav();
            this.setupSearchListener();

            // Display all topics initially
            this.displayTopics(this.allTopics);

            // Hide loading screen
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';

            this.initialized = true;
            console.log('Topical Guide initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Topical Guide:', error);
            document.getElementById('loading-screen').innerHTML =
                `<p style="color: var(--danger-color); text-align: center; padding: 2rem;">
                    Failed to load Topical Guide. Please refresh the page.<br>
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

    async loadAllTopics() {
        console.log('Loading all topics...');

        try {
            const result = this.db.exec(`
                SELECT id, topic_name
                FROM topical_guide_topics
                ORDER BY topic_name
            `);

            if (result.length === 0 || !result[0].values) {
                this.allTopics = [];
                return;
            }

            this.allTopics = result[0].values.map(row => ({
                id: row[0],
                name: row[1]
            }));

            this.filteredTopics = [...this.allTopics];

            // Update count in header
            document.getElementById('topic-count').textContent = this.allTopics.length.toLocaleString();

            console.log(`Loaded ${this.allTopics.length} topics`);
        } catch (error) {
            console.error('Failed to load topics:', error);
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
        const searchInput = document.getElementById('topic-search');

        searchInput.addEventListener('input', (e) => {
            this.searchTopics(e.target.value);
        });
    }

    searchTopics(query) {
        const searchTerm = query.toLowerCase().trim();

        if (searchTerm === '') {
            this.filteredTopics = [...this.allTopics];
        } else {
            this.filteredTopics = this.allTopics.filter(topic =>
                topic.name.toLowerCase().includes(searchTerm)
            );
        }

        this.currentLetter = null;
        this.updateAlphabetButtons();
        this.displayTopics(this.filteredTopics);
        this.updateResultsCount();
    }

    filterByLetter(letter) {
        this.currentLetter = letter;
        this.filteredTopics = this.allTopics.filter(topic =>
            topic.name.toUpperCase().startsWith(letter)
        );

        this.updateAlphabetButtons();
        this.displayTopics(this.filteredTopics);
        this.updateResultsCount();

        // Clear search input
        document.getElementById('topic-search').value = '';
    }

    showAll() {
        this.currentLetter = null;
        this.filteredTopics = [...this.allTopics];

        this.updateAlphabetButtons();
        this.displayTopics(this.filteredTopics);
        this.updateResultsCount();

        // Clear search input
        document.getElementById('topic-search').value = '';
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

    displayTopics(topics) {
        const container = document.getElementById('topic-list');
        const noResults = document.getElementById('no-results');

        if (topics.length === 0) {
            container.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }

        noResults.style.display = 'none';
        container.innerHTML = '';

        topics.forEach(topic => {
            const topicDiv = document.createElement('div');
            topicDiv.className = 'topic-item';
            topicDiv.dataset.topicId = topic.id;

            const header = document.createElement('div');
            header.className = 'topic-header';
            header.innerHTML = `
                <h3 class="topic-title">${this.escapeHtml(topic.name)}</h3>
                <button class="expand-btn" aria-label="Expand topic">+</button>
            `;

            const content = document.createElement('div');
            content.className = 'topic-content';
            content.style.display = 'none';
            content.innerHTML = '<div class="loading-references">Loading references...</div>';

            header.addEventListener('click', () => {
                this.toggleTopic(topic.id, topicDiv, content);
            });

            topicDiv.appendChild(header);
            topicDiv.appendChild(content);
            container.appendChild(topicDiv);
        });
    }

    async toggleTopic(topicId, topicDiv, contentDiv) {
        if (this.expandedTopics.has(topicId)) {
            // Collapse
            this.expandedTopics.delete(topicId);
            contentDiv.style.display = 'none';
            topicDiv.querySelector('.expand-btn').textContent = '+';
            topicDiv.classList.remove('expanded');
        } else {
            // Expand
            this.expandedTopics.add(topicId);
            contentDiv.style.display = 'block';
            topicDiv.querySelector('.expand-btn').textContent = '−';
            topicDiv.classList.add('expanded');

            // Load references if not already loaded
            if (contentDiv.querySelector('.loading-references')) {
                await this.loadTopicReferences(topicId, contentDiv);
            }
        }
    }

    async loadTopicReferences(topicId, contentDiv) {
        try {
            console.log('Loading references for topic ID:', topicId);
            console.log('Database initialized:', this.db !== null);

            if (!this.db) {
                throw new Error('Database not initialized');
            }

            const result = this.db.exec(`
                SELECT scripture_text, citation, collection_name
                FROM topical_guide_references
                WHERE topic_id = ?
                ORDER BY sort_order
            `, [topicId]);

            console.log('Query result:', result);

            if (result.length === 0 || !result[0].values || result[0].values.length === 0) {
                contentDiv.innerHTML = '<p class="no-references">No references found for this topic.</p>';
                return;
            }

            const references = result[0].values.map(row => ({
                excerpt: row[0],        // scripture_text
                citation: row[1],       // citation
                collection: row[2]      // collection_name
            }));

            // Group by collection
            const grouped = this.groupReferencesByCollection(references);

            let html = '';

            // Check if there are "See Also" references (no collection)
            const seeAlsoRefs = references.filter(ref => !ref.collection);
            if (seeAlsoRefs.length > 0) {
                html += '<div class="see-also-section">';
                html += '<h4>See Also</h4>';
                html += '<ul class="see-also-list">';
                seeAlsoRefs.forEach(ref => {
                    html += `<li>${this.escapeHtml(ref.excerpt)}</li>`;
                });
                html += '</ul></div>';
            }

            // Display scripture references by collection
            Object.keys(grouped).forEach(collection => {
                if (collection && collection !== 'null' && collection !== '') {
                    html += `<div class="collection-section">`;
                    html += `<h4>${this.escapeHtml(collection)}</h4>`;
                    html += '<ul class="reference-list">';

                    grouped[collection].forEach(ref => {
                        html += '<li class="scripture-reference">';
                        html += `<span class="reference-text">${this.escapeHtml(ref.excerpt || '')}</span> `;
                        html += `<span class="reference-citation">${this.escapeHtml(ref.citation || ref.reference || '')}</span>`;
                        html += '</li>';
                    });

                    html += '</ul></div>';
                }
            });

            contentDiv.innerHTML = html || '<p class="no-references">No scripture references found.</p>';
        } catch (error) {
            console.error('Failed to load topic references:', error);
            contentDiv.innerHTML = '<p class="error">Failed to load references.</p>';
        }
    }

    groupReferencesByCollection(references) {
        const grouped = {};

        references.forEach(ref => {
            const collection = ref.collection || 'Other';
            if (!grouped[collection]) {
                grouped[collection] = [];
            }
            grouped[collection].push(ref);
        });

        return grouped;
    }

    updateResultsCount() {
        const count = this.filteredTopics.length;
        const countDiv = document.getElementById('search-results-count');

        if (count === this.allTopics.length) {
            countDiv.textContent = `Showing all ${count.toLocaleString()} topics`;
        } else {
            countDiv.textContent = `Showing ${count.toLocaleString()} of ${this.allTopics.length.toLocaleString()} topics`;
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
    const browser = new TopicalGuideBrowser();
    await browser.initialize();
});
