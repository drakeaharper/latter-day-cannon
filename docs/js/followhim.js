/**
 * Follow Him Podcast Viewer
 * Loads and displays Follow Him podcast transcripts from the scripture database
 */

let db = null;
let currentSeries = null;
let currentEpisode = null;
let currentPart = null;
let allParts = []; // All parts for current episode

// Initialize the application
async function init() {
    try {
        await loadDatabase();
        await populateSeries();
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

        const response = await fetch('../followhim.db');
        if (!response.ok) {
            throw new Error('Failed to load database. Make sure you are running a local server.');
        }

        const buffer = await response.arrayBuffer();
        db = new SQL.Database(new Uint8Array(buffer));

        console.log('Follow Him database loaded successfully');
    } catch (error) {
        console.error('Database loading error:', error);
        throw error;
    }
}

// Populate the series dropdown
async function populateSeries() {
    const seriesSelect = document.getElementById('series-select');

    try {
        const results = db.exec(`
            SELECT id, name, year, scripture_focus
            FROM followhim_series
            ORDER BY year DESC, sort_order
        `);

        if (results.length === 0 || results[0].values.length === 0) {
            seriesSelect.innerHTML = '<option value="">No series available</option>';
            return;
        }

        const series = results[0].values;

        seriesSelect.innerHTML = '<option value="">Select a series...</option>';

        series.forEach(([id, name, year, scriptureFocus]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = name;
            option.dataset.year = year;
            option.dataset.focus = scriptureFocus;
            seriesSelect.appendChild(option);
        });

        console.log(`Loaded ${series.length} series`);
    } catch (error) {
        console.error('Error populating series:', error);
    }
}

// Populate episodes for selected series
async function populateEpisodes(seriesId) {
    const episodeSelect = document.getElementById('episode-select');
    const partSelect = document.getElementById('part-select');

    try {
        const results = db.exec(`
            SELECT id, episode_number, title, scripture_reference
            FROM followhim_episodes
            WHERE series_id = ?
            ORDER BY sort_order
        `, [seriesId]);

        episodeSelect.innerHTML = '<option value="">Select an episode...</option>';
        partSelect.innerHTML = '<option value="">Select a part...</option>';
        partSelect.disabled = true;

        if (results.length === 0 || results[0].values.length === 0) {
            episodeSelect.disabled = true;
            return;
        }

        const episodes = results[0].values;

        episodes.forEach(([id, episodeNum, title, scriptureRef]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `Episode ${episodeNum}: ${title}`;
            option.dataset.title = title;
            option.dataset.reference = scriptureRef || '';
            episodeSelect.appendChild(option);
        });

        episodeSelect.disabled = false;
        console.log(`Loaded ${episodes.length} episodes for series ${seriesId}`);
    } catch (error) {
        console.error('Error populating episodes:', error);
    }
}

// Populate parts for selected episode
async function populateParts(episodeId) {
    const partSelect = document.getElementById('part-select');

    try {
        const results = db.exec(`
            SELECT id, part_type, title, guest
            FROM followhim_parts
            WHERE episode_id = ?
            ORDER BY sort_order
        `, [episodeId]);

        partSelect.innerHTML = '<option value="">Select a part...</option>';

        if (results.length === 0 || results[0].values.length === 0) {
            partSelect.disabled = true;
            allParts = [];
            return;
        }

        const parts = results[0].values;
        allParts = parts;

        parts.forEach(([id, partType, title, guest]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = partType + (guest ? ` (${guest})` : '');
            option.dataset.partType = partType;
            option.dataset.guest = guest || '';
            partSelect.appendChild(option);
        });

        partSelect.disabled = false;
        console.log(`Loaded ${parts.length} parts for episode ${episodeId}`);

        // Show episode view with parts
        displayEpisodeView(episodeId);
    } catch (error) {
        console.error('Error populating parts:', error);
    }
}

// Display episode overview with part cards
async function displayEpisodeView(episodeId) {
    try {
        // Get episode info
        const episodeResults = db.exec(`
            SELECT e.episode_number, e.title, e.scripture_reference, s.name as series_name
            FROM followhim_episodes e
            JOIN followhim_series s ON e.series_id = s.id
            WHERE e.id = ?
        `, [episodeId]);

        if (episodeResults.length === 0 || episodeResults[0].values.length === 0) {
            return;
        }

        const [episodeNum, title, scriptureRef, seriesName] = episodeResults[0].values[0];

        // Get all parts for this episode
        const partsResults = db.exec(`
            SELECT id, part_type, title, guest, url
            FROM followhim_parts
            WHERE episode_id = ?
            ORDER BY sort_order
        `, [episodeId]);

        // Update episode header
        document.getElementById('episode-title').textContent = `Episode ${episodeNum}: ${title}`;
        document.getElementById('episode-reference').textContent = scriptureRef || '';

        // Create part cards
        const partsGrid = document.getElementById('parts-grid');

        if (partsResults.length === 0 || partsResults[0].values.length === 0) {
            partsGrid.innerHTML = '<p>No parts available for this episode.</p>';
        } else {
            const parts = partsResults[0].values;

            partsGrid.innerHTML = parts.map(([id, partType, fullTitle, guest, url]) => {
                const icon = partType === 'Part 1' ? '1' :
                            partType === 'Part 2' ? '2' :
                            partType === 'Favorites' ? 'F' : '?';

                return `
                    <div class="part-card" data-part-id="${id}" onclick="displayTranscript(${id})">
                        <div class="part-icon">${icon}</div>
                        <div class="part-info">
                            <h3 class="part-type">${partType}</h3>
                            ${guest ? `<p class="part-guest">${guest}</p>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Show episode view, hide others
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('transcript-display').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('episode-view').style.display = 'block';

        // Scroll to top
        document.querySelector('.fh-reader').scrollTo(0, 0);
    } catch (error) {
        console.error('Error displaying episode view:', error);
    }
}

// Display selected transcript
async function displayTranscript(partId) {
    try {
        const results = db.exec(`
            SELECT
                p.part_type,
                p.title,
                p.guest,
                p.content,
                p.url,
                e.episode_number,
                e.title as episode_title,
                e.scripture_reference,
                s.name as series_name
            FROM followhim_parts p
            JOIN followhim_episodes e ON p.episode_id = e.id
            JOIN followhim_series s ON e.series_id = s.id
            WHERE p.id = ?
        `, [partId]);

        if (results.length === 0 || results[0].values.length === 0) {
            console.error('Transcript not found');
            return;
        }

        const [partType, title, guest, content, url, episodeNum, episodeTitle, scriptureRef, seriesName] = results[0].values[0];

        // Update transcript display
        document.getElementById('transcript-series').textContent = seriesName;
        document.getElementById('transcript-episode').textContent = `Episode ${episodeNum}: ${episodeTitle}`;
        document.getElementById('transcript-title').textContent = title || `${partType}`;
        document.getElementById('guest-name').textContent = guest ? `Guest: ${guest}` : 'Hosts: Hank Smith & John Bytheway';
        document.getElementById('source-link').href = url;

        // Create part tabs for navigation
        const partTabs = document.getElementById('part-tabs');
        partTabs.innerHTML = allParts.map(([id, type, t, g]) => {
            const isActive = id === partId ? 'active' : '';
            return `<button class="part-tab ${isActive}" onclick="displayTranscript(${id})">${type}</button>`;
        }).join('');

        // Format and display content
        const contentDiv = document.getElementById('transcript-content');
        contentDiv.innerHTML = formatTranscriptContent(content);

        // Update part select to match
        document.getElementById('part-select').value = partId;

        // Show transcript display, hide others
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('episode-view').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('transcript-display').style.display = 'block';

        // Scroll to top
        document.querySelector('.fh-reader').scrollTo(0, 0);

        currentPart = partId;

        // Update navigation buttons
        updatePartNavigation();
    } catch (error) {
        console.error('Error displaying transcript:', error);
    }
}

// Format transcript content (convert plain text to HTML)
function formatTranscriptContent(content) {
    if (!content) return '<p>No content available</p>';

    // Split into paragraphs
    const paragraphs = content.split('\n\n');

    return paragraphs.map(para => {
        para = para.trim();
        if (!para) return '';

        // Check if it's a heading (starts with #)
        if (para.startsWith('# ')) {
            return `<h2 class="transcript-heading">${para.substring(2)}</h2>`;
        }

        // Check if it looks like a speaker line (Name: timestamp or Name: text)
        const speakerMatch = para.match(/^([A-Za-z\.\s]+):\s*(\d{1,2}:\d{2}(?::\d{2})?)?(.*)$/);
        if (speakerMatch) {
            const [, speaker, timestamp, text] = speakerMatch;
            const fullText = (timestamp ? timestamp + ' ' : '') + (text || '');
            return `
                <div class="transcript-line">
                    <span class="speaker-label">${speaker.trim()}:</span>
                    <span class="speaker-text">${fullText.trim()}</span>
                </div>
            `;
        }

        // Regular paragraph
        return `<p>${para}</p>`;
    }).join('\n');
}

// Update part navigation buttons
function updatePartNavigation() {
    const currentIndex = allParts.findIndex(p => p[0] === currentPart);

    const prevBtn = document.getElementById('prev-part-btn');
    const nextBtn = document.getElementById('next-part-btn');

    prevBtn.disabled = currentIndex <= 0;
    nextBtn.disabled = currentIndex >= allParts.length - 1;
}

// Navigate between parts
function navigatePart(direction) {
    const currentIndex = allParts.findIndex(p => p[0] === currentPart);
    const newIndex = currentIndex + direction;

    if (newIndex >= 0 && newIndex < allParts.length) {
        const newPartId = allParts[newIndex][0];
        displayTranscript(newPartId);
    }
}

// Search transcripts
async function searchTranscripts(query) {
    if (!query || query.trim().length < 3) {
        alert('Please enter at least 3 characters to search');
        return;
    }

    try {
        const searchTerm = `%${query}%`;

        const results = db.exec(`
            SELECT
                p.id,
                p.part_type,
                p.title,
                p.guest,
                p.content,
                e.episode_number,
                e.title as episode_title,
                s.name as series_name
            FROM followhim_parts p
            JOIN followhim_episodes e ON p.episode_id = e.id
            JOIN followhim_series s ON e.series_id = s.id
            WHERE p.content LIKE ? OR p.title LIKE ? OR p.guest LIKE ? OR e.title LIKE ?
            ORDER BY s.year DESC, e.episode_number, p.sort_order
            LIMIT 50
        `, [searchTerm, searchTerm, searchTerm, searchTerm]);

        if (results.length === 0 || results[0].values.length === 0) {
            displaySearchResults([], query);
            return;
        }

        displaySearchResults(results[0].values, query);
    } catch (error) {
        console.error('Error searching transcripts:', error);
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
        resultsList.innerHTML = results.map(([id, partType, title, guest, content, episodeNum, episodeTitle, seriesName]) => {
            // Create snippet with highlight
            const snippet = createSnippet(content, query, 200);

            return `
                <div class="result-item" onclick="displayTranscript(${id})">
                    <h3 class="result-title">${highlightText(episodeTitle, query)} - ${partType}</h3>
                    <div class="result-meta">
                        <span class="result-series">${seriesName}</span>
                        <span class="result-episode">Episode ${episodeNum}</span>
                        ${guest ? `<span class="result-guest">${highlightText(guest, query)}</span>` : ''}
                    </div>
                    <p class="result-snippet">${snippet}</p>
                </div>
            `;
        }).join('');
    }

    // Show search results
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('episode-view').style.display = 'none';
    document.getElementById('transcript-display').style.display = 'none';
    document.getElementById('search-results').style.display = 'block';

    // Scroll to top
    document.querySelector('.fh-reader').scrollTo(0, 0);
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

// Clear search results
function clearSearch() {
    document.getElementById('fh-search').value = '';
    document.getElementById('search-results').style.display = 'none';
    document.getElementById('welcome-screen').style.display = 'block';
}

// Update statistics
async function updateStats() {
    try {
        // Count series
        const seriesResults = db.exec('SELECT COUNT(*) FROM followhim_series');
        const seriesCount = seriesResults[0].values[0][0];

        // Count episodes
        const episodeResults = db.exec('SELECT COUNT(*) FROM followhim_episodes');
        const episodeCount = episodeResults[0].values[0][0];

        // Count parts (transcripts)
        const partResults = db.exec('SELECT COUNT(*) FROM followhim_parts');
        const partCount = partResults[0].values[0][0];

        document.getElementById('stat-series').textContent = seriesCount;
        document.getElementById('stat-episodes').textContent = episodeCount;
        document.getElementById('stat-parts').textContent = partCount;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Series selection
    document.getElementById('series-select').addEventListener('change', (e) => {
        const seriesId = e.target.value;
        if (seriesId) {
            currentSeries = seriesId;
            populateEpisodes(seriesId);
        } else {
            document.getElementById('episode-select').disabled = true;
            document.getElementById('episode-select').innerHTML = '<option value="">Select an episode...</option>';
            document.getElementById('part-select').disabled = true;
            document.getElementById('part-select').innerHTML = '<option value="">Select a part...</option>';
            // Show welcome screen
            document.getElementById('episode-view').style.display = 'none';
            document.getElementById('transcript-display').style.display = 'none';
            document.getElementById('welcome-screen').style.display = 'block';
        }
    });

    // Episode selection
    document.getElementById('episode-select').addEventListener('change', (e) => {
        const episodeId = e.target.value;
        if (episodeId) {
            currentEpisode = episodeId;
            populateParts(episodeId);
        } else {
            document.getElementById('part-select').disabled = true;
            document.getElementById('part-select').innerHTML = '<option value="">Select a part...</option>';
            allParts = [];
        }
    });

    // Part selection
    document.getElementById('part-select').addEventListener('change', (e) => {
        const partId = e.target.value;
        if (partId) {
            displayTranscript(parseInt(partId));
        } else if (currentEpisode) {
            // If part deselected but episode selected, show episode view
            displayEpisodeView(currentEpisode);
        }
    });

    // Search
    const searchInput = document.getElementById('fh-search');
    const searchBtn = document.getElementById('search-btn');

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            searchTranscripts(query);
        }
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchTranscripts(query);
            }
        }
    });

    // Clear search button
    document.getElementById('clear-search-btn').addEventListener('click', () => {
        clearSearch();
    });

    // Part navigation
    document.getElementById('prev-part-btn').addEventListener('click', () => {
        navigatePart(-1);
    });

    document.getElementById('next-part-btn').addEventListener('click', () => {
        navigatePart(1);
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
