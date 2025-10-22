/**
 * General Conference Viewer
 * Loads and displays General Conference talks from the scripture database
 */

let db = null;
let currentConference = null;
let currentTalk = null;

// Read Tracking using localStorage
class ReadTracker {
    constructor() {
        this.storageKey = 'gc-read-talks';
        this.readTalks = new Set(this.loadFromStorage());
    }

    loadFromStorage() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            return saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Error loading read talks:', error);
            return [];
        }
    }

    saveToStorage() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(Array.from(this.readTalks)));
        } catch (error) {
            console.error('Error saving read talks:', error);
        }
    }

    markAsRead(talkId) {
        this.readTalks.add(talkId);
        this.saveToStorage();
    }

    markAsUnread(talkId) {
        this.readTalks.delete(talkId);
        this.saveToStorage();
    }

    isRead(talkId) {
        return this.readTalks.has(talkId);
    }

    toggleRead(talkId) {
        if (this.isRead(talkId)) {
            this.markAsUnread(talkId);
            return false;
        } else {
            this.markAsRead(talkId);
            return true;
        }
    }

    getReadCount() {
        return this.readTalks.size;
    }

    getAllReadTalks() {
        return Array.from(this.readTalks);
    }

    clearAll() {
        if (confirm('Clear all read status for all talks?')) {
            this.readTalks.clear();
            this.saveToStorage();
            return true;
        }
        return false;
    }
}

const readTracker = new ReadTracker();

// Initialize the application
async function init() {
    try {
        await loadDatabase();
        await populateConferences();
        await updateStats();
        setupEventListeners();
        showMainContent();
    } catch (error) {
        showError(error.message);
    }
}

// Load the SQLite database
async function loadDatabase() {
    try {
        const SQL = await initSqlJs({
            locateFile: file => `https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/${file}`
        });

        const response = await fetch('../scripture-library.db');
        if (!response.ok) {
            throw new Error('Failed to load database. Make sure you are running a local server.');
        }

        const buffer = await response.arrayBuffer();
        db = new SQL.Database(new Uint8Array(buffer));

        console.log('Database loaded successfully');
    } catch (error) {
        console.error('Database loading error:', error);
        throw error;
    }
}

// Populate the conferences dropdown
async function populateConferences() {
    const conferenceSelect = document.getElementById('conference-select');

    try {
        const results = db.exec(`
            SELECT id, year, month, url
            FROM general_conference_conferences
            ORDER BY year DESC, month DESC
        `);

        if (results.length === 0 || results[0].values.length === 0) {
            conferenceSelect.innerHTML = '<option value="">No conferences available</option>';
            return;
        }

        const conferences = results[0].values;

        conferenceSelect.innerHTML = '<option value="">Select a conference...</option>';

        conferences.forEach(([id, year, month, url]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `${month} ${year}`;
            option.dataset.year = year;
            option.dataset.month = month;
            conferenceSelect.appendChild(option);
        });

        console.log(`Loaded ${conferences.length} conferences`);
    } catch (error) {
        console.error('Error populating conferences:', error);
    }
}

// Populate talks for selected conference
async function populateTalks(conferenceId) {
    const talkSelect = document.getElementById('talk-select');

    try {
        const results = db.exec(`
            SELECT id, title, speaker_name, session
            FROM general_conference_talks
            WHERE conference_id = ?
            ORDER BY sort_order
        `, [conferenceId]);

        talkSelect.innerHTML = '<option value="">Select a talk...</option>';

        if (results.length === 0 || results[0].values.length === 0) {
            talkSelect.disabled = true;
            return;
        }

        const talks = results[0].values;

        talks.forEach(([id, title, speaker, session]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `${title} - ${speaker}`;
            option.dataset.session = session || '';
            talkSelect.appendChild(option);
        });

        talkSelect.disabled = false;
        console.log(`Loaded ${talks.length} talks for conference ${conferenceId}`);

        // Show talk list view by default
        displayTalkListView(conferenceId);
    } catch (error) {
        console.error('Error populating talks:', error);
    }
}

// Display talk list view
async function displayTalkListView(conferenceId) {
    try {
        // Get conference info
        const confResults = db.exec(`
            SELECT year, month
            FROM general_conference_conferences
            WHERE id = ?
        `, [conferenceId]);

        if (confResults.length === 0 || confResults[0].values.length === 0) {
            return;
        }

        const [year, month] = confResults[0].values[0];

        // Get all talks for this conference
        const talkResults = db.exec(`
            SELECT id, title, speaker_name, speaker_calling, session
            FROM general_conference_talks
            WHERE conference_id = ?
            ORDER BY sort_order
        `, [conferenceId]);

        if (talkResults.length === 0 || talkResults[0].values.length === 0) {
            return;
        }

        const talks = talkResults[0].values;

        // Update conference title
        document.getElementById('conference-title').textContent = `${month} ${year} General Conference`;

        // Create talk cards
        const talksGrid = document.getElementById('talks-grid');
        talksGrid.innerHTML = talks.map(([id, title, speaker, calling, session]) => {
            const isRead = readTracker.isRead(id);
            const readClass = isRead ? 'read' : '';
            const checkedClass = isRead ? 'checked' : '';

            return `
                <div class="talk-card ${readClass}" data-talk-id="${id}">
                    <div class="talk-card-header">
                        <h3 class="talk-card-title">${title}</h3>
                        <div class="read-toggle ${checkedClass}"
                             data-talk-id="${id}"
                             onclick="event.stopPropagation(); toggleReadStatus(${id})"></div>
                    </div>
                    <p class="talk-card-speaker">${speaker}</p>
                    ${calling ? `<p class="talk-card-calling">${calling}</p>` : ''}
                    ${session ? `<div class="talk-card-session">Session: ${session}</div>` : ''}
                </div>
            `;
        }).join('');

        // Add click handlers to cards (not to read toggles)
        document.querySelectorAll('.talk-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('read-toggle')) {
                    const talkId = card.dataset.talkId;
                    displayTalk(parseInt(talkId));
                }
            });
        });

        // Show talk list view, hide others
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('talk-display').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('talk-list-view').style.display = 'block';

        // Scroll to top
        document.querySelector('.gc-reader').scrollTo(0, 0);
    } catch (error) {
        console.error('Error displaying talk list:', error);
    }
}

// Display selected talk
async function displayTalk(talkId) {
    try {
        const results = db.exec(`
            SELECT
                t.title,
                t.speaker_name,
                t.speaker_calling,
                t.session,
                t.content,
                t.url,
                c.year,
                c.month
            FROM general_conference_talks t
            JOIN general_conference_conferences c ON t.conference_id = c.id
            WHERE t.id = ?
        `, [talkId]);

        if (results.length === 0 || results[0].values.length === 0) {
            console.error('Talk not found');
            return;
        }

        const [title, speaker, calling, session, content, url, year, month] = results[0].values[0];

        // Update talk display
        document.getElementById('talk-conference').textContent = `${month} ${year}`;
        document.getElementById('talk-session').textContent = session || '';
        document.getElementById('talk-title').textContent = title;
        document.getElementById('speaker-name').textContent = speaker;
        document.getElementById('speaker-calling').textContent = calling || '';
        document.getElementById('source-link').href = url;

        // Format and display content
        const contentDiv = document.getElementById('talk-content');
        contentDiv.innerHTML = formatTalkContent(content);

        // Show talk display, hide others
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('talk-list-view').style.display = 'none';
        document.getElementById('talk-display').style.display = 'block';

        // Scroll to top
        document.querySelector('.gc-reader').scrollTo(0, 0);

        currentTalk = talkId;
    } catch (error) {
        console.error('Error displaying talk:', error);
    }
}

// Toggle read status for a talk
function toggleReadStatus(talkId) {
    const isNowRead = readTracker.toggleRead(talkId);

    // Update UI - find all elements for this talk
    const card = document.querySelector(`.talk-card[data-talk-id="${talkId}"]`);
    const toggle = document.querySelector(`.read-toggle[data-talk-id="${talkId}"]`);

    if (card && toggle) {
        if (isNowRead) {
            card.classList.add('read');
            toggle.classList.add('checked');
        } else {
            card.classList.remove('read');
            toggle.classList.remove('checked');
        }
    }

    console.log(`Talk ${talkId} marked as ${isNowRead ? 'read' : 'unread'}`);
}

// Clear all read status for current conference only
function clearAllReadStatus() {
    if (!currentConference) {
        return;
    }

    if (!confirm('Clear read status for all talks in this conference?')) {
        return;
    }

    try {
        // Get all talk IDs from the current conference
        const talkResults = db.exec(`
            SELECT id
            FROM general_conference_talks
            WHERE conference_id = ?
        `, [currentConference]);

        if (talkResults.length === 0 || talkResults[0].values.length === 0) {
            return;
        }

        const talkIds = talkResults[0].values.map(row => row[0]);

        // Mark each talk as unread
        talkIds.forEach(talkId => {
            readTracker.markAsUnread(talkId);
        });

        // Refresh the talk list view
        displayTalkListView(currentConference);

        console.log(`Cleared read status for ${talkIds.length} talks in current conference`);
    } catch (error) {
        console.error('Error clearing read status:', error);
    }
}

// Format talk content (convert plain text to HTML with proper formatting)
function formatTalkContent(content) {
    if (!content) return '<p>No content available</p>';

    // Split into paragraphs and format
    const paragraphs = content.split('\n\n');

    return paragraphs.map(para => {
        para = para.trim();
        if (!para) return '';

        // Check if it's a heading
        if (para.startsWith('## ')) {
            return `<h2>${para.substring(3)}</h2>`;
        }

        // Check if it's a blockquote
        if (para.startsWith('> ')) {
            return `<blockquote>${para.substring(2)}</blockquote>`;
        }

        // Regular paragraph
        return `<p>${para}</p>`;
    }).join('\n');
}

// Search talks
async function searchTalks(query) {
    if (!query || query.trim().length < 3) {
        alert('Please enter at least 3 characters to search');
        return;
    }

    try {
        const searchTerm = `%${query}%`;

        const results = db.exec(`
            SELECT
                t.id,
                t.title,
                t.speaker_name,
                t.content,
                c.year,
                c.month
            FROM general_conference_talks t
            JOIN general_conference_conferences c ON t.conference_id = c.id
            WHERE t.title LIKE ? OR t.content LIKE ? OR t.speaker_name LIKE ?
            ORDER BY c.year DESC, c.month DESC, t.sort_order
            LIMIT 50
        `, [searchTerm, searchTerm, searchTerm]);

        if (results.length === 0 || results[0].values.length === 0) {
            displaySearchResults([], query);
            return;
        }

        displaySearchResults(results[0].values, query);
    } catch (error) {
        console.error('Error searching talks:', error);
    }
}

// Display search results
function displaySearchResults(results, query) {
    const resultsCount = document.getElementById('results-count');
    const resultsList = document.getElementById('results-list');

    resultsCount.textContent = `Found ${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"`;

    if (results.length === 0) {
        resultsList.innerHTML = '<p>No results found. Try different search terms.</p>';
    } else {
        resultsList.innerHTML = results.map(([id, title, speaker, content, year, month]) => {
            // Create snippet with highlight
            const snippet = createSnippet(content, query, 200);

            return `
                <div class="result-item" onclick="displayTalk(${id})">
                    <h3 class="result-title">${highlightText(title, query)}</h3>
                    <div class="result-meta">
                        <span class="result-conference">${month} ${year}</span>
                        <span class="result-speaker">${highlightText(speaker, query)}</span>
                    </div>
                    <p class="result-snippet">${snippet}</p>
                </div>
            `;
        }).join('');
    }

    // Show search results
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('talk-display').style.display = 'none';
    document.getElementById('search-results').style.display = 'block';

    // Scroll to top
    document.querySelector('.gc-reader').scrollTo(0, 0);
}

// Create snippet with context around search term
function createSnippet(text, query, maxLength) {
    if (!text) return '';

    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    const index = lowerText.indexOf(lowerQuery);

    if (index === -1) {
        // Query not found in text, return beginning
        return highlightText(text.substring(0, maxLength), query) + '...';
    }

    // Calculate start and end positions for snippet
    const start = Math.max(0, index - Math.floor(maxLength / 2));
    const end = Math.min(text.length, start + maxLength);

    let snippet = text.substring(start, end);

    if (start > 0) snippet = '...' + snippet;
    if (end < text.length) snippet = snippet + '...';

    return highlightText(snippet, query);
}

// Highlight query in text
function highlightText(text, query) {
    if (!query) return text;

    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

// Escape special regex characters
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Update statistics
async function updateStats() {
    try {
        // Count conferences
        const confResults = db.exec('SELECT COUNT(*) FROM general_conference_conferences');
        const conferenceCount = confResults[0].values[0][0];

        // Count talks
        const talkResults = db.exec('SELECT COUNT(*) FROM general_conference_talks');
        const talkCount = talkResults[0].values[0][0];

        document.getElementById('stat-conferences').textContent = conferenceCount;
        document.getElementById('stat-talks').textContent = talkCount;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Conference selection
    document.getElementById('conference-select').addEventListener('change', (e) => {
        const conferenceId = e.target.value;
        if (conferenceId) {
            currentConference = conferenceId;
            populateTalks(conferenceId);
        } else {
            document.getElementById('talk-select').disabled = true;
            document.getElementById('talk-select').innerHTML = '<option value="">Select a talk...</option>';
            // Hide talk list view
            document.getElementById('talk-list-view').style.display = 'none';
            document.getElementById('welcome-screen').style.display = 'block';
        }
    });

    // Talk selection
    document.getElementById('talk-select').addEventListener('change', (e) => {
        const talkId = e.target.value;
        if (talkId) {
            displayTalk(parseInt(talkId));
        } else if (currentConference) {
            // If talk deselected but conference selected, show list view
            displayTalkListView(currentConference);
        }
    });

    // Search
    const searchInput = document.getElementById('gc-search');
    const searchBtn = document.getElementById('search-btn');

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            searchTalks(query);
        }
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchTalks(query);
            }
        }
    });

    // Clear all read status button
    document.getElementById('clear-read-status-btn').addEventListener('click', () => {
        clearAllReadStatus();
    });
}

// Show main content
function showMainContent() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('main-content').style.display = 'flex';
}

// Show error
function showError(message) {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-screen').style.display = 'flex';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
