// draggable-window.js

class DraggableWindow extends HTMLElement {
    constructor() {
        super();

        // Create a shadow DOM
        this.attachShadow({mode: 'open'});

        // Window state
        this._isMinimized = false;
        this._isMaximized = false;
        this._originalStyles = {};

        // Instance variables for dragging
        this._isDragging = false;
        this._isResizing = false;
        this._resizeHandle = null;
        this._startX = 0;
        this._startY = 0;
        this._startWidth = 0;
        this._startHeight = 0;
        this._startLeft = 0;
        this._startTop = 0;

        // Create the window structure
        this._createWindowStructure();

        // Initialize event listeners
        this._initializeEventListeners();
    }

    // Lifecycle methods
    connectedCallback() {
        // Set default attributes if not provided
        if (!this.hasAttribute('window-title')) {
            this.setAttribute('window-title', 'Window');
        }

        if (!this.style.width) {
            this.style.width = '300px';
        }

        if (!this.style.height) {
            this.style.height = '200px';
        }

        if (!this.style.left) {
            this.style.left = '50px';
        }

        if (!this.style.top) {
            this.style.top = '50px';
        }

        // Add to window manager
        WindowManager.addWindow(this);

        // Focus this window when connected
        this.bringToFront();
    }

    disconnectedCallback() {
        // Remove from window manager
        WindowManager.removeWindow(this);
    }

    // Observed attributes
    static get observedAttributes() {
        return ['window-title', 'minimizable', 'maximizable', 'closable'];
    }

    // Attribute changed callback
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'window-title' && this._titleElement) {
            this._titleElement.textContent = newValue;
        } else if (name === 'minimizable') {
            this._toggleButton(this._minimizeButton, newValue !== 'false');
        } else if (name === 'maximizable') {
            this._toggleButton(this._maximizeButton, newValue !== 'false');
        } else if (name === 'closable') {
            this._toggleButton(this._closeButton, newValue !== 'false');
        }
    }

    // Private methods
    _createWindowStructure() {
        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
      :host {
        position: absolute;
        display: flex;
        flex-direction: column;
        min-width: 100px;
        min-height: 55px;
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        overflow: hidden;
        transition: box-shadow 0.2s ease;
        z-index: 1;
        touch-action: none;
      }
      
      :host(.active) {
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
        z-index: 2;
      }
      
      .window-header {
        display: flex;
        align-items: center;
        padding: 4px 8px;
        background-color: #f0f0f0;
        border-bottom: 1px solid #cccccc;
        user-select: none;
        cursor: move;
        height: 32px;
      }
      
      .window-title {
        flex-grow: 1;
        font-family: sans-serif;
        font-size: 14px;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .window-controls {
        display: flex;
        gap: 4px;
      }
      
      .window-button {
        width: 24px;
        height: 24px;
        border: none;
        border-radius: 4px;
        background-color: transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        outline: none;
      }
      
      .window-button:hover {
        background-color: rgba(0, 0, 0, 0.1);
      }
      
      .window-button.close:hover {
        background-color: #ff5252;
        color: white;
      }
      
      .window-content {
        flex-grow: 1;
        overflow: auto;
        padding: 16px;
        position: relative;
      }
      
      .resize-handle {
        position: absolute;
        background: transparent;
      }
      
      .resize-handle-tl { 
        top: 0; 
        left: 0; 
        width: 12px; 
        height: 12px; 
        cursor: nwse-resize; 
      }
      
      .resize-handle-tr { 
        top: 0; 
        right: 0; 
        width: 12px; 
        height: 12px; 
        cursor: nesw-resize; 
      }
      
      .resize-handle-bl { 
        bottom: 0; 
        left: 0; 
        width: 12px; 
        height: 12px; 
        cursor: nesw-resize; 
      }
      
      .resize-handle-br { 
        bottom: 0; 
        right: 0; 
        width: 12px; 
        height: 12px; 
        cursor: nwse-resize; 
      }
      
      .resize-handle-t { 
        top: 0; 
        left: 12px; 
        right: 12px; 
        height: 6px; 
        cursor: ns-resize; 
      }
      
      .resize-handle-b { 
        bottom: 0; 
        left: 12px; 
        right: 12px; 
        height: 6px; 
        cursor: ns-resize; 
      }
      
      .resize-handle-l { 
        left: 0; 
        top: 12px; 
        bottom: 12px; 
        width: 6px; 
        cursor: ew-resize; 
      }
      
      .resize-handle-r { 
        right: 0; 
        top: 12px; 
        bottom: 12px; 
        width: 6px; 
        cursor: ew-resize; 
      }
      
      :host(.minimized) {
        display: none;
      }
      
      :host(.maximized) {
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        border-radius: 0;
      }
    `;

        // Create window elements
        const header = document.createElement('div');
        header.className = 'window-header';

        this._titleElement = document.createElement('h3');
        this._titleElement.className = 'window-title';
        this._titleElement.textContent = this.getAttribute('window-title') || 'Window';

        const controls = document.createElement('div');
        controls.className = 'window-controls';

        this._minimizeButton = document.createElement('button');
        this._minimizeButton.className = 'window-button minimize';
        this._minimizeButton.innerHTML = '&#8211;';
        this._minimizeButton.setAttribute('aria-label', 'Minimize');

        this._maximizeButton = document.createElement('button');
        this._maximizeButton.className = 'window-button maximize';
        this._maximizeButton.innerHTML = '&#9744;';
        this._maximizeButton.setAttribute('aria-label', 'Maximize');

        this._closeButton = document.createElement('button');
        this._closeButton.className = 'window-button close';
        this._closeButton.innerHTML = '&#10005;';
        this._closeButton.setAttribute('aria-label', 'Close');

        controls.appendChild(this._minimizeButton);
        controls.appendChild(this._maximizeButton);
        controls.appendChild(this._closeButton);

        header.appendChild(this._titleElement);
        header.appendChild(controls);

        const content = document.createElement('div');
        content.className = 'window-content';
        content.setAttribute('tabindex', '0');

        // Create resize handles
        const resizeHandles = [
            {class: 'resize-handle resize-handle-tl', position: 'tl'},
            {class: 'resize-handle resize-handle-tr', position: 'tr'},
            {class: 'resize-handle resize-handle-bl', position: 'bl'},
            {class: 'resize-handle resize-handle-br', position: 'br'},
            {class: 'resize-handle resize-handle-t', position: 't'},
            {class: 'resize-handle resize-handle-b', position: 'b'},
            {class: 'resize-handle resize-handle-l', position: 'l'},
            {class: 'resize-handle resize-handle-r', position: 'r'}
        ];

        // Build shadow DOM
        this.shadowRoot.appendChild(style);
        this.shadowRoot.appendChild(header);
        this.shadowRoot.appendChild(content);

        // Add resize handles
        resizeHandles.forEach(handle => {
            const el = document.createElement('div');
            el.className = handle.class;
            el.dataset.position = handle.position;
            this.shadowRoot.appendChild(el);
        });

        // Move the main content to the content area
        const slot = document.createElement('slot');
        content.appendChild(slot);

        // Store elements for reference
        this._headerElement = header;
        this._contentElement = content;
    }

    _initializeEventListeners() {
        // Window header drag
        this._headerElement.addEventListener('pointerdown', this._onHeaderPointerDown.bind(this));

        // Window controls
        this._minimizeButton.addEventListener('click', this.minimize.bind(this));
        this._maximizeButton.addEventListener('click', this.toggleMaximize.bind(this));
        this._closeButton.addEventListener('click', this.close.bind(this));

        // Focus handling
        this.addEventListener('pointerdown', this.bringToFront.bind(this));

        // Handle resize pointers
        const resizeHandles = this.shadowRoot.querySelectorAll('.resize-handle');
        resizeHandles.forEach(handle => {
            handle.addEventListener('pointerdown', this._onResizePointerDown.bind(this));
        });

        // For double-click on header to maximize
        this._headerElement.addEventListener('dblclick', this.toggleMaximize.bind(this));

        // Escape key to close (optional, depends on your requirements)
        this.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.classList.contains('active')) {
                this.close();
            }
        });
    }

    _toggleButton(button, show) {
        if (button) {
            button.style.display = show ? 'flex' : 'none';
        }
    }

    _onHeaderPointerDown(e) {
        // Ignore if we clicked on a button
        if (e.target.closest('.window-button')) {
            return;
        }

        this.bringToFront();

        if (this._isMaximized) {
            return;
        }

        // Explicitly prevent default to stop any browser behaviors
        e.preventDefault();

        // Store pointer ID for tracking
        this._pointerId = e.pointerId;

        // Start dragging
        this._isDragging = true;
        this._startX = e.clientX;
        this._startY = e.clientY;
        this._startLeft = this.offsetLeft;
        this._startTop = this.offsetTop;

        // Capture pointer for smooth dragging
        this._headerElement.setPointerCapture(e.pointerId);

        // Define bound functions as instance properties so they can be properly removed later
        if (!this._boundDragMove) {
            this._boundDragMove = this._onDragPointerMove.bind(this);
            this._boundDragUp = this._onDragPointerUp.bind(this);
        }

        // Add event listeners for move and up
        this._headerElement.addEventListener('pointermove', this._boundDragMove);
        this._headerElement.addEventListener('pointerup', this._boundDragUp);
        this._headerElement.addEventListener('pointercancel', this._boundDragUp);
    }

    _onDragPointerMove(e) {
        if (!this._isDragging || e.pointerId !== this._pointerId) return;

        // Prevent default to ensure smooth dragging
        e.preventDefault();

        const dx = e.clientX - this._startX;
        const dy = e.clientY - this._startY;

        const newLeft = this._startLeft + dx;
        const newTop = this._startTop + dy;

        this.style.left = `${newLeft}px`;
        this.style.top = `${newTop}px`;
    }

    _onDragPointerUp(e) {
        if (!this._isDragging || e.pointerId !== this._pointerId) return;

        this._isDragging = false;

        // Release the pointer capture
        try {
            this._headerElement.releasePointerCapture(e.pointerId);
        } catch (err) {
            // Ignore errors if the capture was already released
        }

        // Remove event listeners
        this._headerElement.removeEventListener('pointermove', this._boundDragMove);
        this._headerElement.removeEventListener('pointerup', this._boundDragUp);
        this._headerElement.removeEventListener('pointercancel', this._boundDragUp);
    }

    _onResizePointerDown(e) {
        if (this._isMaximized) return;

        e.stopPropagation();
        this.bringToFront();

        // Prevent default browser behaviors
        e.preventDefault();

        // Store pointer ID for tracking
        this._resizePointerId = e.pointerId;

        this._isResizing = true;
        this._resizeHandle = e.target.dataset.position;
        this._startX = e.clientX;
        this._startY = e.clientY;
        this._startWidth = this.offsetWidth;
        this._startHeight = this.offsetHeight;
        this._startLeft = this.offsetLeft;
        this._startTop = this.offsetTop;

        // Capture pointer for smooth resizing
        e.target.setPointerCapture(e.pointerId);

        // Define bound functions as instance properties
        if (!this._boundResizeMove) {
            this._boundResizeMove = this._onResizePointerMove.bind(this);
            this._boundResizeUp = this._onResizePointerUp.bind(this);
        }

        // Add event listeners for move and up
        e.target.addEventListener('pointermove', this._boundResizeMove);
        e.target.addEventListener('pointerup', this._boundResizeUp);
        e.target.addEventListener('pointercancel', this._boundResizeUp);
    }

    _onResizePointerMove(e) {
        if (!this._isResizing || e.pointerId !== this._resizePointerId) return;

        // Prevent default to ensure smooth resizing
        e.preventDefault();

        const dx = e.clientX - this._startX;
        const dy = e.clientY - this._startY;
        const minWidth = 100;
        const minHeight = 55;

        let newWidth = this._startWidth;
        let newHeight = this._startHeight;
        let newLeft = this._startLeft;
        let newTop = this._startTop;

        // Handle resizing based on the handle position
        switch (this._resizeHandle) {
            case 'tl': // top-left
                newWidth = Math.max(minWidth, this._startWidth - dx);
                newHeight = Math.max(minHeight, this._startHeight - dy);
                newLeft = this._startLeft + (this._startWidth - newWidth);
                newTop = this._startTop + (this._startHeight - newHeight);
                break;

            case 'tr': // top-right
                newWidth = Math.max(minWidth, this._startWidth + dx);
                newHeight = Math.max(minHeight, this._startHeight - dy);
                newTop = this._startTop + (this._startHeight - newHeight);
                break;

            case 'bl': // bottom-left
                newWidth = Math.max(minWidth, this._startWidth - dx);
                newHeight = Math.max(minHeight, this._startHeight + dy);
                newLeft = this._startLeft + (this._startWidth - newWidth);
                break;

            case 'br': // bottom-right
                newWidth = Math.max(minWidth, this._startWidth + dx);
                newHeight = Math.max(minHeight, this._startHeight + dy);
                break;

            case 't': // top
                newHeight = Math.max(minHeight, this._startHeight - dy);
                newTop = this._startTop + (this._startHeight - newHeight);
                break;

            case 'b': // bottom
                newHeight = Math.max(minHeight, this._startHeight + dy);
                break;

            case 'l': // left
                newWidth = Math.max(minWidth, this._startWidth - dx);
                newLeft = this._startLeft + (this._startWidth - newWidth);
                break;

            case 'r': // right
                newWidth = Math.max(minWidth, this._startWidth + dx);
                break;
        }

        // Apply new dimensions and position
        this.style.width = `${newWidth}px`;
        this.style.height = `${newHeight}px`;
        this.style.left = `${newLeft}px`;
        this.style.top = `${newTop}px`;
    }

    _onResizePointerUp(e) {
        if (!this._isResizing || e.pointerId !== this._resizePointerId) return;

        this._isResizing = false;
        this._resizeHandle = null;

        // Release the pointer capture
        try {
            e.target.releasePointerCapture(e.pointerId);
        } catch (err) {
            // Ignore errors if the capture was already released
        }

        // Remove event listeners
        e.target.removeEventListener('pointermove', this._boundResizeMove);
        e.target.removeEventListener('pointerup', this._boundResizeUp);
        e.target.removeEventListener('pointercancel', this._boundResizeUp);
    }

    // Public methods
    bringToFront() {
        WindowManager.bringToFront(this);
    }

    minimize() {
        if (this._isMinimized) return;

        this._isMinimized = true;
        this.classList.add('minimized');

        // Dispatch event
        this.dispatchEvent(new CustomEvent('minimize', {bubbles: true}));

        // Update button and ARIA state
        this._minimizeButton.setAttribute('aria-label', 'Restore');

        // Remove active state since window is now minimized
        this.classList.remove('active');
        WindowManager.windowMinimized(this);
    }

    restore() {
        if (this._isMinimized) {
            this._isMinimized = false;
            this.classList.remove('minimized');

            // Dispatch event
            this.dispatchEvent(new CustomEvent('restore', {bubbles: true}));

            // Update button and ARIA state
            this._minimizeButton.setAttribute('aria-label', 'Minimize');

            // Bring to front when restored
            this.bringToFront();
        } else if (this._isMaximized) {
            this._isMaximized = false;
            this.classList.remove('maximized');

            // Restore previous size and position
            Object.assign(this.style, this._originalStyles);

            // Update button and ARIA state
            this._maximizeButton.innerHTML = '&#9744;';
            this._maximizeButton.setAttribute('aria-label', 'Maximize');

            // Dispatch event
            this.dispatchEvent(new CustomEvent('restore', {bubbles: true}));
        }
    }

    maximize() {
        if (this._isMaximized || this._isMinimized) return;

        // Store current size and position for restoration
        this._originalStyles = {
            top: this.style.top,
            left: this.style.left,
            width: this.style.width,
            height: this.style.height
        };

        this._isMaximized = true;
        this.classList.add('maximized');

        // Dispatch event
        this.dispatchEvent(new CustomEvent('maximize', {bubbles: true}));

        // Update button and ARIA state
        this._maximizeButton.innerHTML = '&#9783;';
        this._maximizeButton.setAttribute('aria-label', 'Restore');
    }

    toggleMaximize() {
        if (this._isMaximized) {
            this.restore();
        } else {
            this.maximize();
        }
    }

    close() {
        // Dispatch event before removal
        this.dispatchEvent(new CustomEvent('close', {bubbles: true}));

        // Remove from DOM
        if (this.parentNode) {
            this.parentNode.removeChild(this);
        }
    }

    // Getters/setters
    get title() {
        return this.getAttribute('window-title');
    }

    set title(value) {
        this.setAttribute('window-title', value);
    }

    get minimizable() {
        return this.getAttribute('minimizable') !== 'false';
    }

    set minimizable(value) {
        this.setAttribute('minimizable', value.toString());
    }

    get maximizable() {
        return this.getAttribute('maximizable') !== 'false';
    }

    set maximizable(value) {
        this.setAttribute('maximizable', value.toString());
    }

    get closable() {
        return this.getAttribute('closable') !== 'false';
    }

    set closable(value) {
        this.setAttribute('closable', value.toString());
    }
}

// Window Manager to handle multiple windows
class WindowManager {
    static _windows = new Set();
    static _highestZIndex = 100;
    static _minimizedWindows = new Set();

    static addWindow(window) {
        this._windows.add(window);
    }

    static removeWindow(window) {
        this._windows.delete(window);
        this._minimizedWindows.delete(window);
    }

    static bringToFront(window) {
        // Increment z-index counter
        this._highestZIndex += 1;

        // Set the window's z-index
        window.style.zIndex = this._highestZIndex;

        // Remove active class from all windows
        this._windows.forEach(win => {
            win.classList.remove('active');
        });

        // Add active class to this window
        window.classList.add('active');

        // Focus the window content
        window.shadowRoot.querySelector('.window-content').focus();
    }

    static windowMinimized(window) {
        this._minimizedWindows.add(window);
    }

    static getTotalWindows() {
        return this._windows.size;
    }

    static getMinimizedWindows() {
        return this._minimizedWindows;
    }

    static restoreAllWindows() {
        this._minimizedWindows.forEach(window => {
            window.restore();
        });
        this._minimizedWindows.clear();
    }
}

// Register the custom element
customElements.define('draggable-window', DraggableWindow);

// Create a Taskbar component (optional)
class WindowTaskbar extends HTMLElement {
    constructor() {
        super();

        // Create a shadow DOM
        this.attachShadow({mode: 'open'});

        // Create the taskbar structure
        this._createTaskbarStructure();

        // Initialize
        this._minimizedWindowsList = new Map();
    }

    connectedCallback() {
        // Listen for window minimize events
        document.addEventListener('minimize', this._handleWindowMinimize.bind(this));
        document.addEventListener('close', this._handleWindowClose.bind(this));
        document.addEventListener('restore', this._handleWindowRestore.bind(this));
    }

    disconnectedCallback() {
        // Remove event listeners
        document.removeEventListener('minimize', this._handleWindowMinimize.bind(this));
        document.removeEventListener('close', this._handleWindowClose.bind(this));
        document.removeEventListener('restore', this._handleWindowRestore.bind(this));
    }

    _createTaskbarStructure() {
        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
      :host {
        display: block;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40px;
        background-color: #f0f0f0;
        border-top: 1px solid #cccccc;
        box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        padding: 0 16px;
        z-index: 1000;
      }
      
      .taskbar-items {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        flex-grow: 1;
      }
      
      .taskbar-item {
        padding: 4px 12px;
        background-color: #e0e0e0;
        border-radius: 4px;
        font-family: sans-serif;
        font-size: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
        cursor: pointer;
        user-select: none;
      }
      
      .taskbar-item:hover {
        background-color: #d0d0d0;
      }
    `;

        // Create taskbar elements
        const taskbarItems = document.createElement('div');
        taskbarItems.className = 'taskbar-items';

        // Build shadow DOM
        this.shadowRoot.appendChild(style);
        this.shadowRoot.appendChild(taskbarItems);

        // Store for reference
        this._taskbarItems = taskbarItems;
    }

    _handleWindowMinimize(e) {
        const window = e.target;
        if (window instanceof DraggableWindow) {
            // Create a taskbar item for this window
            const item = document.createElement('div');
            item.className = 'taskbar-item';
            item.textContent = window.title;
            item.addEventListener('click', () => {
                window.restore();
            });

            // Store a reference
            this._minimizedWindowsList.set(window, item);

            // Add to taskbar
            this._taskbarItems.appendChild(item);
        }
    }

    _handleWindowClose(e) {
        const window = e.target;
        if (this._minimizedWindowsList.has(window)) {
            const item = this._minimizedWindowsList.get(window);
            this._taskbarItems.removeChild(item);
            this._minimizedWindowsList.delete(window);
        }
    }

    _handleWindowRestore(e) {
        const window = e.target;
        if (this._minimizedWindowsList.has(window)) {
            const item = this._minimizedWindowsList.get(window);
            this._taskbarItems.removeChild(item);
            this._minimizedWindowsList.delete(window);
        }
    }
}

// Register the taskbar component
customElements.define('window-taskbar', WindowTaskbar);

// Export API
window.WindowSystem = {
    DraggableWindow,
    WindowTaskbar,
    WindowManager
};