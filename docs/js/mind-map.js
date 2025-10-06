// Mind Map Application
class MindMap {
    constructor() {
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.mode = 'select'; // 'select', 'add-node', 'add-connection'
        this.connectionStart = null;
        this.draggedNode = null;
        this.dragOffset = { x: 0, y: 0 };
        this.dragStartPos = null;
        this.hasDragged = false;
        this.nodeIdCounter = 0;
        this.currentMapName = null;
        this.autoSaveInterval = null;
        this.hasUnsavedChanges = false;
        this.originalNodeState = null;

        this.canvas = document.getElementById('mind-map-canvas');
        this.nodesLayer = document.getElementById('nodes-layer');
        this.connectionsLayer = document.getElementById('connections-layer');
        this.nodeEditor = document.getElementById('node-editor');

        this.nodeTypeColors = {
            topic: '#3498db',
            scripture: '#2ecc71',
            insight: '#f39c12',
            question: '#e74c3c',
            note: '#9b59b6'
        };

        this.initializeEventListeners();
        this.startAutoSave();
        this.initializeBeforeUnload();
    }

    initializeEventListeners() {
        // Toolbar buttons
        document.getElementById('add-node-btn').addEventListener('click', () => {
            this.setMode('add-node');
        });

        document.getElementById('add-connection-btn').addEventListener('click', () => {
            this.setMode('add-connection');
        });

        document.getElementById('clear-map-btn').addEventListener('click', () => {
            if (confirm('Are you sure you want to clear the entire mind map?')) {
                this.clearMap();
            }
        });

        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportMap();
        });

        document.getElementById('import-btn').addEventListener('click', () => {
            document.getElementById('import-file-input').click();
        });

        document.getElementById('import-file-input').addEventListener('change', (e) => {
            this.importMap(e.target.files[0]);
        });

        // Canvas interactions
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // Node editor
        document.getElementById('save-node-btn').addEventListener('click', () => {
            this.saveNodeEdit();
        });

        document.getElementById('delete-node-btn').addEventListener('click', () => {
            this.deleteNode();
        });

        document.getElementById('cancel-edit-btn').addEventListener('click', () => {
            this.closeNodeEditor();
        });

        // Node type selector for color update (preview only, not saved until Save button)
        document.getElementById('node-type').addEventListener('change', () => {
            if (this.selectedNode) {
                const newType = document.getElementById('node-type').value;
                this.selectedNode.type = newType;
                this.updateNodeDisplay(this.selectedNode);
                // Don't mark as changed here - only mark when Save is clicked
            }
        });
    }

    setMode(mode) {
        this.mode = mode;
        this.connectionStart = null;

        // Update cursor
        if (mode === 'add-node') {
            this.canvas.style.cursor = 'crosshair';
        } else if (mode === 'add-connection') {
            this.canvas.style.cursor = 'pointer';
        } else {
            this.canvas.style.cursor = 'default';
        }

        // Visual feedback
        document.querySelectorAll('.toolbar button').forEach(btn => {
            btn.style.opacity = '1';
        });
    }

    handleCanvasClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.mode === 'add-node') {
            this.addNode(x, y);
            this.setMode('select');
        } else if (this.mode === 'add-connection') {
            const clickedNode = this.getNodeAtPosition(x, y);
            if (clickedNode) {
                if (!this.connectionStart) {
                    this.connectionStart = clickedNode;
                } else {
                    if (this.connectionStart !== clickedNode) {
                        this.addConnection(this.connectionStart, clickedNode);
                    }
                    this.connectionStart = null;
                    this.setMode('select');
                }
            }
        }
    }

    handleMouseDown(e) {
        if (this.mode !== 'select') return;

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const clickedNode = this.getNodeAtPosition(x, y);
        if (clickedNode) {
            this.draggedNode = clickedNode;
            this.dragStartPos = { x, y };
            this.hasDragged = false;
            this.dragOffset = {
                x: x - clickedNode.x,
                y: y - clickedNode.y
            };
            this.canvas.style.cursor = 'grabbing';
        }
    }

    handleMouseMove(e) {
        if (!this.draggedNode) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Check if mouse has moved (more than 1 pixel)
        const dx = Math.abs(x - this.dragStartPos.x);
        const dy = Math.abs(y - this.dragStartPos.y);

        if (dx > 1 || dy > 1) {
            this.hasDragged = true;
        }

        this.draggedNode.x = x - this.dragOffset.x;
        this.draggedNode.y = y - this.dragOffset.y;

        this.updateNodeDisplay(this.draggedNode);
        this.updateConnectionsForNode(this.draggedNode);
    }

    handleMouseUp(e) {
        if (this.draggedNode) {
            if (this.hasDragged) {
                // Node was dragged
                this.markAsChanged();
            } else {
                // Node was clicked without dragging - open editor
                this.editNode(this.draggedNode);
            }

            this.draggedNode = null;
            this.dragStartPos = null;
            this.hasDragged = false;
            this.canvas.style.cursor = 'default';
        }
    }

    addNode(x, y) {
        const node = {
            id: this.nodeIdCounter++,
            x: x,
            y: y,
            title: 'New Node',
            description: '',
            type: 'topic',
            shape: document.getElementById('node-shape').value,
            color: document.getElementById('node-color').value
        };

        this.nodes.push(node);
        this.renderNode(node);
        this.markAsChanged();
    }

    renderNode(node) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.classList.add('mind-map-node');
        group.setAttribute('data-node-id', node.id);

        // Determine shape
        let shape;
        const width = 120;
        const height = 60;

        if (node.shape === 'circle') {
            shape = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            shape.setAttribute('cx', node.x);
            shape.setAttribute('cy', node.y);
            shape.setAttribute('rx', width / 2);
            shape.setAttribute('ry', height / 2);
        } else if (node.shape === 'rectangle') {
            shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            shape.setAttribute('x', node.x - width / 2);
            shape.setAttribute('y', node.y - height / 2);
            shape.setAttribute('width', width);
            shape.setAttribute('height', height);
        } else { // rounded
            shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            shape.setAttribute('x', node.x - width / 2);
            shape.setAttribute('y', node.y - height / 2);
            shape.setAttribute('width', width);
            shape.setAttribute('height', height);
            shape.setAttribute('rx', 10);
            shape.setAttribute('ry', 10);
        }

        const color = this.nodeTypeColors[node.type] || node.color;
        shape.classList.add('node-shape');
        shape.setAttribute('fill', color);

        // Text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.classList.add('node-text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y);
        text.textContent = this.truncateText(node.title, 15);

        group.appendChild(shape);
        group.appendChild(text);

        // Note: Click to edit is now handled in handleMouseUp
        // No need for double-click listener

        this.nodesLayer.appendChild(group);
    }

    updateNodeDisplay(node) {
        const group = this.nodesLayer.querySelector(`[data-node-id="${node.id}"]`);
        if (!group) return;

        const shape = group.querySelector('.node-shape');
        const text = group.querySelector('.node-text');

        const width = 120;
        const height = 60;

        // Update position based on shape
        if (node.shape === 'circle') {
            shape.setAttribute('cx', node.x);
            shape.setAttribute('cy', node.y);
        } else {
            shape.setAttribute('x', node.x - width / 2);
            shape.setAttribute('y', node.y - height / 2);
        }

        // Update color
        const color = this.nodeTypeColors[node.type] || node.color;
        shape.setAttribute('fill', color);

        // Update text
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y);
        text.textContent = this.truncateText(node.title, 15);
    }

    addConnection(fromNode, toNode) {
        const connection = {
            id: `${fromNode.id}-${toNode.id}`,
            from: fromNode.id,
            to: toNode.id
        };

        // Check if connection already exists
        if (this.connections.some(c => c.from === fromNode.id && c.to === toNode.id)) {
            return;
        }

        this.connections.push(connection);
        this.renderConnection(connection);
        this.markAsChanged();
    }

    renderConnection(connection) {
        const fromNode = this.nodes.find(n => n.id === connection.from);
        const toNode = this.nodes.find(n => n.id === connection.to);

        if (!fromNode || !toNode) return;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.classList.add('connection-line');
        line.setAttribute('data-connection-id', connection.id);
        line.setAttribute('x1', fromNode.x);
        line.setAttribute('y1', fromNode.y);
        line.setAttribute('x2', toNode.x);
        line.setAttribute('y2', toNode.y);

        this.connectionsLayer.appendChild(line);
    }

    updateConnectionsForNode(node) {
        this.connections.forEach(connection => {
            if (connection.from === node.id || connection.to === node.id) {
                const line = this.connectionsLayer.querySelector(`[data-connection-id="${connection.id}"]`);
                if (line) {
                    const fromNode = this.nodes.find(n => n.id === connection.from);
                    const toNode = this.nodes.find(n => n.id === connection.to);

                    if (fromNode && toNode) {
                        line.setAttribute('x1', fromNode.x);
                        line.setAttribute('y1', fromNode.y);
                        line.setAttribute('x2', toNode.x);
                        line.setAttribute('y2', toNode.y);
                    }
                }
            }
        });
    }

    editNode(node) {
        this.selectedNode = node;
        // Store original state for cancel functionality
        this.originalNodeState = {
            title: node.title,
            description: node.description,
            type: node.type
        };
        document.getElementById('node-title').value = node.title;
        document.getElementById('node-description').value = node.description;
        document.getElementById('node-type').value = node.type;
        this.nodeEditor.classList.remove('hidden');
    }

    saveNodeEdit() {
        if (!this.selectedNode) return;

        this.selectedNode.title = document.getElementById('node-title').value;
        this.selectedNode.description = document.getElementById('node-description').value;
        this.selectedNode.type = document.getElementById('node-type').value;

        this.updateNodeDisplay(this.selectedNode);
        this.originalNodeState = null; // Clear original state since we're saving
        this.selectedNode = null;
        this.nodeEditor.classList.add('hidden');
        this.markAsChanged();
    }

    deleteNode() {
        if (!this.selectedNode) return;

        // Remove connections
        this.connections = this.connections.filter(c => {
            if (c.from === this.selectedNode.id || c.to === this.selectedNode.id) {
                const line = this.connectionsLayer.querySelector(`[data-connection-id="${c.id}"]`);
                if (line) line.remove();
                return false;
            }
            return true;
        });

        // Remove node
        const group = this.nodesLayer.querySelector(`[data-node-id="${this.selectedNode.id}"]`);
        if (group) group.remove();

        this.nodes = this.nodes.filter(n => n.id !== this.selectedNode.id);
        this.closeNodeEditor();
        this.markAsChanged();
    }

    closeNodeEditor() {
        // Revert changes if there was an original state (cancel was pressed)
        if (this.selectedNode && this.originalNodeState) {
            this.selectedNode.title = this.originalNodeState.title;
            this.selectedNode.description = this.originalNodeState.description;
            this.selectedNode.type = this.originalNodeState.type;
            this.updateNodeDisplay(this.selectedNode);
        }
        this.selectedNode = null;
        this.originalNodeState = null;
        this.nodeEditor.classList.add('hidden');
    }

    getNodeAtPosition(x, y) {
        for (let node of this.nodes) {
            const distance = Math.sqrt(Math.pow(x - node.x, 2) + Math.pow(y - node.y, 2));
            if (distance < 60) { // Approximate hit area
                return node;
            }
        }
        return null;
    }

    clearMap() {
        this.nodes = [];
        this.connections = [];
        this.nodesLayer.innerHTML = '';
        this.connectionsLayer.innerHTML = '';
        this.closeNodeEditor();
        this.markAsChanged();
    }

    exportMap() {
        const data = {
            nodes: this.nodes,
            connections: this.connections
        };

        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `mind-map-${this.currentMapName || Date.now()}.json`;
        a.click();

        URL.revokeObjectURL(url);
    }

    importMap(file) {
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.clearMap();

                this.nodes = data.nodes || [];
                this.connections = data.connections || [];

                // Update counter
                this.nodeIdCounter = Math.max(...this.nodes.map(n => n.id), 0) + 1;

                // Render all
                this.nodes.forEach(node => this.renderNode(node));
                this.connections.forEach(connection => this.renderConnection(connection));

                this.markAsChanged();
            } catch (error) {
                alert('Error importing mind map: ' + error.message);
            }
        };
        reader.readAsText(file);
    }

    // Database integration methods

    async saveCurrentMap() {
        if (!this.currentMapName) {
            this.promptSaveAs();
            return;
        }

        const mapData = {
            nodes: this.nodes,
            connections: this.connections
        };

        const success = await dbManager.saveMindMap(this.currentMapName, mapData);
        if (success) {
            this.hasUnsavedChanges = false;
            this.updateTitle();
            console.log(`Saved map: ${this.currentMapName}`);
        } else {
            alert('Failed to save mind map');
        }
    }

    async promptSaveAs() {
        const name = prompt('Enter a name for this mind map:');
        if (!name || name.trim() === '') return;

        this.currentMapName = name.trim();
        await this.saveCurrentMap();
        this.refreshMapList();
    }

    async loadMap(name) {
        // Check for unsaved changes
        if (this.hasUnsavedChanges) {
            if (!confirm('You have unsaved changes. Load anyway?')) {
                return;
            }
        }

        const mapData = await dbManager.loadMindMap(name);
        if (!mapData) {
            alert('Failed to load mind map');
            return;
        }

        this.clearMap();
        this.currentMapName = name;
        this.nodes = mapData.data.nodes || [];
        this.connections = mapData.data.connections || [];

        // Update counter
        this.nodeIdCounter = Math.max(...this.nodes.map(n => n.id), 0) + 1;

        // Render all
        this.nodes.forEach(node => this.renderNode(node));
        this.connections.forEach(connection => this.renderConnection(connection));

        this.hasUnsavedChanges = false;
        this.updateTitle();
        console.log(`Loaded map: ${name}`);
    }

    async newMap() {
        // Check for unsaved changes
        if (this.hasUnsavedChanges) {
            if (!confirm('You have unsaved changes. Create new map anyway?')) {
                return;
            }
        }

        this.clearMap();
        this.currentMapName = null;
        this.hasUnsavedChanges = false;
        this.updateTitle();
    }

    async deleteMap(name) {
        if (!confirm(`Delete mind map "${name}"?`)) {
            return;
        }

        const success = await dbManager.deleteMindMap(name);
        if (success) {
            if (this.currentMapName === name) {
                this.newMap();
            }
            this.refreshMapList();
        } else {
            alert('Failed to delete mind map');
        }
    }

    async refreshMapList() {
        const maps = await dbManager.getAllMindMaps();
        const listContainer = document.getElementById('map-list');
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (maps.length === 0) {
            listContainer.innerHTML = '<p class="no-maps">No saved maps yet</p>';
            return;
        }

        maps.forEach(map => {
            const item = document.createElement('div');
            item.className = 'map-list-item';
            if (map.name === this.currentMapName) {
                item.classList.add('active');
            }

            const nameSpan = document.createElement('span');
            nameSpan.textContent = map.name;
            nameSpan.className = 'map-name';
            nameSpan.addEventListener('click', () => this.loadMap(map.name));

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '×';
            deleteBtn.className = 'delete-map-btn';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteMap(map.name);
            });

            item.appendChild(nameSpan);
            item.appendChild(deleteBtn);
            listContainer.appendChild(item);
        });
    }

    markAsChanged() {
        this.hasUnsavedChanges = true;
        this.updateTitle();
    }

    updateTitle() {
        const titleElement = document.getElementById('current-map-title');
        if (titleElement) {
            const name = this.currentMapName || 'Untitled Map';
            const unsaved = this.hasUnsavedChanges ? ' *' : '';
            titleElement.textContent = name + unsaved;
        }
    }

    startAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            if (this.hasUnsavedChanges && this.currentMapName) {
                this.saveCurrentMap();
            }
        }, 30000);
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }

    initializeBeforeUnload() {
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges) {
                // Modern browsers require returnValue to be set
                e.preventDefault();
                e.returnValue = '';
                // Some browsers show this message, others show a generic message
                return 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }
}

// Global mind map instance
let mindMap = null;

// Initialize the mind map when page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Show loading indicator
    console.log('Initializing Scripture Study Helper...');

    // Initialize database first
    const dbReady = await dbManager.initialize();
    if (!dbReady) {
        console.warn('Database initialization failed. Running in limited mode.');
        console.warn('Save/Load features will not be available. You can still use Export/Import.');
        // Don't show alert, just log warning - the app can still work with export/import
    } else {
        console.log('Database initialized successfully!');
    }

    // Create mind map instance
    mindMap = new MindMap();

    // Set up map management event listeners
    document.getElementById('save-map-btn')?.addEventListener('click', async () => {
        if (!dbManager.initialized) {
            alert('Database not available. Use Export instead.');
            return;
        }
        await mindMap.saveCurrentMap();
    });

    document.getElementById('save-as-btn')?.addEventListener('click', async () => {
        if (!dbManager.initialized) {
            alert('Database not available. Use Export instead.');
            return;
        }
        await mindMap.promptSaveAs();
    });

    document.getElementById('new-map-btn')?.addEventListener('click', async () => {
        await mindMap.newMap();
    });

    document.getElementById('toggle-map-list-btn')?.addEventListener('click', () => {
        if (!dbManager.initialized) {
            alert('Database not available. Saved maps feature requires database initialization.');
            return;
        }
        const sidebar = document.getElementById('map-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('hidden');
            if (!sidebar.classList.contains('hidden')) {
                mindMap.refreshMapList();
            }
        }
    });

    document.getElementById('close-sidebar-btn')?.addEventListener('click', () => {
        const sidebar = document.getElementById('map-sidebar');
        if (sidebar) {
            sidebar.classList.add('hidden');
        }
    });

    document.getElementById('toggle-info-btn')?.addEventListener('click', () => {
        const content = document.getElementById('info-content');
        const button = document.getElementById('toggle-info-btn');
        if (content && button) {
            content.classList.toggle('collapsed');
            button.textContent = content.classList.contains('collapsed') ? '+' : '−';
        }
    });

    // Initial map list refresh (only if DB is ready)
    if (dbManager.initialized) {
        mindMap.refreshMapList();
    }

    console.log('Scripture Study Helper ready!');
});
