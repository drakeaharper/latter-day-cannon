// SQLite Database Manager using sql.js
class DatabaseManager {
    constructor() {
        this.db = null;
        this.SQL = null;
        this.initialized = false;
    }

    async initialize() {
        try {
            console.log('Starting database initialization...');

            // Wait for sql.js to load if needed
            let initSqlJs = window.initSqlJs;

            if (!initSqlJs) {
                console.log('Waiting for sql.js to load from CDN...');
                // Wait for the script to load (up to 10 seconds)
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
            } else {
                console.log('sql.js already loaded');
            }

            console.log('Initializing SQL.js...');
            this.SQL = await initSqlJs({
                locateFile: file => {
                    const url = `https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/${file}`;
                    console.log(`Loading SQL.js file: ${url}`);
                    return url;
                }
            });
            console.log('SQL.js initialized');

            // Try to load existing database from localStorage
            const savedDb = localStorage.getItem('scripture-study-db');

            if (savedDb) {
                console.log('Loading existing database from localStorage...');
                // Load existing database
                const uint8Array = new Uint8Array(JSON.parse(savedDb));
                this.db = new this.SQL.Database(uint8Array);
                console.log('Loaded existing database from localStorage');
            } else {
                console.log('Creating new database...');
                // Create new database
                this.db = new this.SQL.Database();
                this.createSchema();
                console.log('Created new database');
            }

            this.initialized = true;
            console.log('Database initialization complete!');
            return true;
        } catch (error) {
            console.error('Failed to initialize database:', error);
            console.error('Error details:', error.message);
            console.error('Error stack:', error.stack);
            return false;
        }
    }

    createSchema() {
        // Mind maps table
        this.db.run(`
            CREATE TABLE IF NOT EXISTS mind_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // Create an index on name for faster lookups
        this.db.run(`
            CREATE INDEX IF NOT EXISTS idx_mind_maps_name
            ON mind_maps(name)
        `);

        // Create full-text search virtual table for searching within maps
        this.db.run(`
            CREATE VIRTUAL TABLE IF NOT EXISTS mind_map_search
            USING fts5(map_id, map_name, content)
        `);

        console.log('Database schema created');
        this.saveToLocalStorage();
    }

    saveToLocalStorage() {
        if (!this.db) return;

        try {
            // Export database to Uint8Array
            const data = this.db.export();
            // Convert to regular array for JSON serialization
            const array = Array.from(data);
            localStorage.setItem('scripture-study-db', JSON.stringify(array));
        } catch (error) {
            console.error('Failed to save database to localStorage:', error);
        }
    }

    // Mind Map Operations

    async saveMindMap(name, mapData) {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        const dataJson = JSON.stringify(mapData);

        try {
            // Check if map exists
            const exists = this.db.exec(`
                SELECT id FROM mind_maps WHERE name = ?
            `, [name]);

            if (exists.length > 0) {
                // Update existing map
                this.db.run(`
                    UPDATE mind_maps
                    SET data = ?, modified_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                `, [dataJson, name]);
            } else {
                // Insert new map
                this.db.run(`
                    INSERT INTO mind_maps (name, data)
                    VALUES (?, ?)
                `, [name, dataJson]);
            }

            // Update search index
            this.updateSearchIndex(name, mapData);

            this.saveToLocalStorage();
            return true;
        } catch (error) {
            console.error('Failed to save mind map:', error);
            return false;
        }
    }

    async loadMindMap(name) {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        try {
            const result = this.db.exec(`
                SELECT data, created_at, modified_at
                FROM mind_maps
                WHERE name = ?
            `, [name]);

            if (result.length === 0 || result[0].values.length === 0) {
                return null;
            }

            const [data, created_at, modified_at] = result[0].values[0];

            return {
                name: name,
                data: JSON.parse(data),
                created_at: created_at,
                modified_at: modified_at
            };
        } catch (error) {
            console.error('Failed to load mind map:', error);
            return null;
        }
    }

    async getAllMindMaps() {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        try {
            const result = this.db.exec(`
                SELECT id, name, created_at, modified_at
                FROM mind_maps
                ORDER BY modified_at DESC
            `);

            if (result.length === 0) {
                return [];
            }

            return result[0].values.map(row => ({
                id: row[0],
                name: row[1],
                created_at: row[2],
                modified_at: row[3]
            }));
        } catch (error) {
            console.error('Failed to get all mind maps:', error);
            return [];
        }
    }

    async deleteMindMap(name) {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        try {
            this.db.run(`DELETE FROM mind_maps WHERE name = ?`, [name]);

            // Remove from search index
            this.db.run(`DELETE FROM mind_map_search WHERE map_name = ?`, [name]);

            this.saveToLocalStorage();
            return true;
        } catch (error) {
            console.error('Failed to delete mind map:', error);
            return false;
        }
    }

    async renameMindMap(oldName, newName) {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        try {
            this.db.run(`
                UPDATE mind_maps
                SET name = ?, modified_at = CURRENT_TIMESTAMP
                WHERE name = ?
            `, [newName, oldName]);

            // Update search index
            this.db.run(`
                UPDATE mind_map_search
                SET map_name = ?
                WHERE map_name = ?
            `, [newName, oldName]);

            this.saveToLocalStorage();
            return true;
        } catch (error) {
            console.error('Failed to rename mind map:', error);
            return false;
        }
    }

    updateSearchIndex(mapName, mapData) {
        try {
            // Remove old search entries for this map
            this.db.run(`DELETE FROM mind_map_search WHERE map_name = ?`, [mapName]);

            // Get map ID
            const result = this.db.exec(`SELECT id FROM mind_maps WHERE name = ?`, [mapName]);
            if (result.length === 0 || result[0].values.length === 0) return;

            const mapId = result[0].values[0][0];

            // Build searchable content from nodes
            const searchContent = mapData.nodes.map(node => {
                return `${node.title} ${node.description} ${node.type}`;
            }).join(' ');

            // Insert into search index
            this.db.run(`
                INSERT INTO mind_map_search (map_id, map_name, content)
                VALUES (?, ?, ?)
            `, [mapId, mapName, searchContent]);

        } catch (error) {
            console.error('Failed to update search index:', error);
        }
    }

    async searchMindMaps(query) {
        if (!this.initialized) {
            throw new Error('Database not initialized');
        }

        try {
            const result = this.db.exec(`
                SELECT DISTINCT map_name
                FROM mind_map_search
                WHERE content MATCH ?
            `, [query]);

            if (result.length === 0) {
                return [];
            }

            return result[0].values.map(row => row[0]);
        } catch (error) {
            console.error('Failed to search mind maps:', error);
            return [];
        }
    }

    // Utility methods

    async exportDatabase() {
        if (!this.db) return null;

        const data = this.db.export();
        const blob = new Blob([data], { type: 'application/x-sqlite3' });
        return blob;
    }

    async importDatabase(file) {
        try {
            const arrayBuffer = await file.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);

            // Close current database
            if (this.db) {
                this.db.close();
            }

            // Load new database
            this.db = new this.SQL.Database(uint8Array);
            this.saveToLocalStorage();

            return true;
        } catch (error) {
            console.error('Failed to import database:', error);
            return false;
        }
    }

    async clearAllData() {
        if (confirm('This will delete ALL your mind maps. Are you sure?')) {
            try {
                this.db.run(`DELETE FROM mind_maps`);
                this.db.run(`DELETE FROM mind_map_search`);
                this.saveToLocalStorage();
                return true;
            } catch (error) {
                console.error('Failed to clear data:', error);
                return false;
            }
        }
        return false;
    }
}

// Create global database instance
const dbManager = new DatabaseManager();
