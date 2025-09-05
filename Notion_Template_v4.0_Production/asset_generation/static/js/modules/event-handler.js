/**
 * Estate Planning v4.0 - Event Handler Module
 * Manages all event binding and user interactions
 */

class EmotionalConfigEventHandler {
    constructor(manager) {
        this.manager = manager; // Reference to main EmotionalConfigManager
        this.eventListeners = new Map();
        this.initialized = false;
    }

    /**
     * Initialize all event handlers
     */
    initialize() {
        if (this.initialized) {
            console.warn('Event handlers already initialized');
            return;
        }

        this.bindNavigationEvents();
        this.bindToneEvents();
        this.bindStyleEvents();
        this.bindFormEvents();
        this.bindUtilityEvents();
        this.bindKeyboardEvents();
        
        this.initialized = true;
        console.log('Event handlers initialized');
    }

    /**
     * Bind navigation and main action events
     */
    bindNavigationEvents() {
        // Load configuration button
        this.addEventHandler('#load-config-btn', 'click', async (e) => {
            e.preventDefault();
            await this.manager.loadConfiguration();
        });

        // Save configuration button
        this.addEventHandler('#save-config-btn', 'click', async (e) => {
            e.preventDefault();
            await this.manager.saveConfiguration();
        });

        // Reset to defaults button
        this.addEventHandler('#reset-defaults-btn', 'click', async (e) => {
            e.preventDefault();
            if (confirm('Are you sure you want to reset all configurations to defaults? This action cannot be undone.')) {
                await this.manager.resetToDefaults();
            }
        });

        // Preview changes button
        this.addEventHandler('#preview-changes-btn', 'click', async (e) => {
            e.preventDefault();
            await this.manager.previewChanges();
        });

        // Generate test assets button
        this.addEventHandler('#generate-test-btn', 'click', async (e) => {
            e.preventDefault();
            await this.manager.generateTestAssets();
        });
    }

    /**
     * Bind emotional tone related events
     */
    bindToneEvents() {
        // Intensity slider changes
        this.addEventHandler(document, 'input', (e) => {
            if (e.target.classList.contains('intensity-range')) {
                const toneName = e.target.dataset.tone;
                const intensity = parseFloat(e.target.value);
                this.handleIntensityChange(toneName, intensity);
            }
        });

        // Add keyword events
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.classList.contains('add-keyword-btn')) {
                e.preventDefault();
                const toneName = e.target.dataset.tone;
                const input = document.querySelector(`.add-keyword-input[data-tone="${toneName}"]`);
                if (input && input.value.trim()) {
                    this.handleAddKeyword(toneName, input.value.trim());
                    input.value = '';
                }
            }
        });

        // Remove keyword events
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.classList.contains('remove-keyword')) {
                e.preventDefault();
                const keyword = e.target.dataset.keyword;
                const toneCard = e.target.closest('.tone-card');
                const toneName = toneCard ? toneCard.dataset.tone : null;
                if (toneName && keyword) {
                    this.handleRemoveKeyword(toneName, keyword);
                }
            }
        });

        // Add keyword on Enter key
        this.addEventHandler(document, 'keypress', (e) => {
            if (e.target.classList.contains('add-keyword-input') && e.key === 'Enter') {
                e.preventDefault();
                const toneName = e.target.dataset.tone;
                if (e.target.value.trim()) {
                    this.handleAddKeyword(toneName, e.target.value.trim());
                    e.target.value = '';
                }
            }
        });
    }

    /**
     * Bind style elements related events
     */
    bindStyleEvents() {
        // Add style element events
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.classList.contains('add-element-btn')) {
                e.preventDefault();
                const categoryName = e.target.dataset.category;
                const input = document.querySelector(`.add-element-input[data-category="${categoryName}"]`);
                if (input && input.value.trim()) {
                    this.handleAddStyleElement(categoryName, input.value.trim());
                    input.value = '';
                }
            }
        });

        // Remove style element events
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.classList.contains('remove-element')) {
                e.preventDefault();
                const element = e.target.dataset.element;
                const categoryContainer = e.target.closest('.style-category');
                const categoryName = categoryContainer ? categoryContainer.dataset.category : null;
                if (categoryName && element) {
                    this.handleRemoveStyleElement(categoryName, element);
                }
            }
        });

        // Add style element on Enter key
        this.addEventHandler(document, 'keypress', (e) => {
            if (e.target.classList.contains('add-element-input') && e.key === 'Enter') {
                e.preventDefault();
                const categoryName = e.target.dataset.category;
                if (e.target.value.trim()) {
                    this.handleAddStyleElement(categoryName, e.target.value.trim());
                    e.target.value = '';
                }
            }
        });
    }

    /**
     * Bind form and validation events
     */
    bindFormEvents() {
        // Form submission prevention
        this.addEventHandler('form', 'submit', (e) => {
            e.preventDefault();
            console.log('Form submission prevented - using AJAX instead');
        });

        // Input validation and sanitization
        this.addEventHandler(document, 'blur', (e) => {
            if (e.target.matches('input[type="text"], textarea')) {
                this.handleInputValidation(e.target);
            }
        });

        // Real-time character limits
        this.addEventHandler(document, 'input', (e) => {
            if (e.target.matches('input[type="text"], textarea')) {
                this.handleCharacterLimit(e.target);
            }
        });
    }

    /**
     * Bind utility and helper events
     */
    bindUtilityEvents() {
        // Modal close events
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.matches('[data-bs-dismiss="modal"]')) {
                // Let Bootstrap handle modal dismissal
                console.log('Modal dismiss triggered');
            }
        });

        // Tooltip and popover initialization
        this.addEventHandler(document, 'mouseenter', (e) => {
            if (e.target.matches('[data-bs-toggle="tooltip"]')) {
                this.initializeTooltip(e.target);
            }
        });

        // Tab switching
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.matches('[data-bs-toggle="tab"]')) {
                this.handleTabSwitch(e.target);
            }
        });

        // Copy to clipboard functionality
        this.addEventHandler(document, 'click', (e) => {
            if (e.target.matches('.copy-btn, [data-action="copy"]')) {
                e.preventDefault();
                this.handleCopyToClipboard(e.target);
            }
        });
    }

    /**
     * Bind keyboard shortcuts and accessibility events
     */
    bindKeyboardEvents() {
        // Global keyboard shortcuts
        this.addEventHandler(document, 'keydown', (e) => {
            // Ctrl+S / Cmd+S - Save configuration
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.manager.saveConfiguration();
                return;
            }

            // Ctrl+L / Cmd+L - Load configuration
            if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
                e.preventDefault();
                this.manager.loadConfiguration();
                return;
            }

            // Ctrl+P / Cmd+P - Preview changes
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                this.manager.previewChanges();
                return;
            }

            // Escape key - Cancel current operation
            if (e.key === 'Escape') {
                this.handleEscapeKey();
                return;
            }
        });

        // Focus management for accessibility
        this.addEventHandler(document, 'keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
    }

    /**
     * Event handler methods
     */
    handleIntensityChange(toneName, intensity) {
        if (!this.manager.domRenderer) return;
        
        console.log(`Intensity changed for ${toneName}: ${intensity}`);
        this.manager.domRenderer.updateToneIntensity(toneName, intensity);
        
        // Update configuration data
        if (this.manager.currentConfig && this.manager.currentConfig.emotional_tones) {
            if (!this.manager.currentConfig.emotional_tones[toneName]) {
                this.manager.currentConfig.emotional_tones[toneName] = {};
            }
            this.manager.currentConfig.emotional_tones[toneName].intensity = intensity;
        }

        // Trigger change event for auto-save if enabled
        this.triggerConfigurationChange('intensity', { toneName, intensity });
    }

    handleAddKeyword(toneName, keyword) {
        if (!this.manager.domRenderer || !this.manager.dataValidator) return;
        
        // Validate and sanitize keyword
        const sanitizedKeyword = this.manager.dataValidator.sanitizeInput(keyword);
        if (!this.manager.dataValidator.validateKeyword(sanitizedKeyword)) {
            this.manager.uiNotifications?.showError('Invalid keyword. Keywords must be 1-50 characters and contain only letters, numbers, spaces, and basic punctuation.');
            return;
        }

        // Add to DOM
        const added = this.manager.domRenderer.addKeywordToTone(toneName, sanitizedKeyword);
        if (!added) {
            this.manager.uiNotifications?.showWarning('Keyword already exists or could not be added.');
            return;
        }

        // Update configuration data
        if (this.manager.currentConfig && this.manager.currentConfig.emotional_tones) {
            if (!this.manager.currentConfig.emotional_tones[toneName]) {
                this.manager.currentConfig.emotional_tones[toneName] = {};
            }
            if (!this.manager.currentConfig.emotional_tones[toneName].keywords) {
                this.manager.currentConfig.emotional_tones[toneName].keywords = [];
            }
            this.manager.currentConfig.emotional_tones[toneName].keywords.push(sanitizedKeyword);
        }

        console.log(`Added keyword "${sanitizedKeyword}" to tone "${toneName}"`);
        this.triggerConfigurationChange('keyword_add', { toneName, keyword: sanitizedKeyword });
    }

    handleRemoveKeyword(toneName, keyword) {
        if (!this.manager.domRenderer) return;
        
        // Remove from DOM
        const removed = this.manager.domRenderer.removeKeywordFromTone(toneName, keyword);
        if (!removed) {
            console.warn('Keyword not found in DOM:', keyword);
            return;
        }

        // Update configuration data
        if (this.manager.currentConfig && 
            this.manager.currentConfig.emotional_tones &&
            this.manager.currentConfig.emotional_tones[toneName] &&
            this.manager.currentConfig.emotional_tones[toneName].keywords) {
            
            const index = this.manager.currentConfig.emotional_tones[toneName].keywords.indexOf(keyword);
            if (index > -1) {
                this.manager.currentConfig.emotional_tones[toneName].keywords.splice(index, 1);
            }
        }

        console.log(`Removed keyword "${keyword}" from tone "${toneName}"`);
        this.triggerConfigurationChange('keyword_remove', { toneName, keyword });
    }

    handleAddStyleElement(categoryName, element) {
        if (!this.manager.domRenderer || !this.manager.dataValidator) return;
        
        // Validate and sanitize element
        const sanitizedElement = this.manager.dataValidator.sanitizeInput(element);
        if (!this.manager.dataValidator.validateStyleElement(sanitizedElement)) {
            this.manager.uiNotifications?.showError('Invalid style element. Elements must be 1-100 characters and contain only letters, numbers, spaces, and basic punctuation.');
            return;
        }

        // Add to DOM
        const added = this.manager.domRenderer.addStyleElement(categoryName, sanitizedElement);
        if (!added) {
            this.manager.uiNotifications?.showWarning('Style element already exists or could not be added.');
            return;
        }

        // Update configuration data
        if (this.manager.currentConfig && this.manager.currentConfig.style_elements) {
            if (!this.manager.currentConfig.style_elements[categoryName]) {
                this.manager.currentConfig.style_elements[categoryName] = [];
            }
            this.manager.currentConfig.style_elements[categoryName].push(sanitizedElement);
        }

        console.log(`Added style element "${sanitizedElement}" to category "${categoryName}"`);
        this.triggerConfigurationChange('style_add', { categoryName, element: sanitizedElement });
    }

    handleRemoveStyleElement(categoryName, element) {
        if (!this.manager.domRenderer) return;
        
        // Remove from DOM
        const removed = this.manager.domRenderer.removeStyleElement(categoryName, element);
        if (!removed) {
            console.warn('Style element not found in DOM:', element);
            return;
        }

        // Update configuration data
        if (this.manager.currentConfig && 
            this.manager.currentConfig.style_elements &&
            this.manager.currentConfig.style_elements[categoryName]) {
            
            const index = this.manager.currentConfig.style_elements[categoryName].indexOf(element);
            if (index > -1) {
                this.manager.currentConfig.style_elements[categoryName].splice(index, 1);
            }
        }

        console.log(`Removed style element "${element}" from category "${categoryName}"`);
        this.triggerConfigurationChange('style_remove', { categoryName, element });
    }

    handleInputValidation(input) {
        if (!this.manager.dataValidator) return;
        
        const value = input.value;
        const sanitized = this.manager.dataValidator.sanitizeInput(value);
        
        if (value !== sanitized) {
            input.value = sanitized;
            this.manager.uiNotifications?.showInfo('Input was automatically cleaned for security.');
        }

        // Add validation visual feedback
        const isValid = sanitized.length > 0 && sanitized.length <= (input.dataset.maxLength || 100);
        
        input.classList.remove('is-valid', 'is-invalid');
        input.classList.add(isValid ? 'is-valid' : 'is-invalid');
    }

    handleCharacterLimit(input) {
        const maxLength = parseInt(input.dataset.maxLength) || 100;
        const currentLength = input.value.length;
        
        // Find or create character counter
        let counter = input.parentNode.querySelector('.char-counter');
        if (!counter) {
            counter = document.createElement('small');
            counter.className = 'char-counter text-muted';
            input.parentNode.appendChild(counter);
        }
        
        counter.textContent = `${currentLength}/${maxLength}`;
        counter.classList.toggle('text-danger', currentLength > maxLength);
        
        // Truncate if over limit
        if (currentLength > maxLength) {
            input.value = input.value.substring(0, maxLength);
            counter.textContent = `${maxLength}/${maxLength}`;
        }
    }

    handleEscapeKey() {
        // Close any open modals
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) modal.hide();
            return;
        }

        // Clear any active inputs
        const activeInput = document.activeElement;
        if (activeInput && activeInput.matches('input, textarea')) {
            activeInput.blur();
            return;
        }

        // Cancel any loading operations
        if (this.manager.currentOperation) {
            console.log('Operation cancelled by user');
            // Implementation depends on operation type
        }
    }

    handleTabNavigation(e) {
        // Enhance accessibility by ensuring proper tab order
        const focusableElements = document.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        
        const focusableArray = Array.from(focusableElements);
        const currentIndex = focusableArray.indexOf(document.activeElement);
        
        if (e.shiftKey && currentIndex === 0) {
            // Wrap to last element
            e.preventDefault();
            focusableArray[focusableArray.length - 1].focus();
        } else if (!e.shiftKey && currentIndex === focusableArray.length - 1) {
            // Wrap to first element
            e.preventDefault();
            focusableArray[0].focus();
        }
    }

    handleTabSwitch(tabElement) {
        const targetId = tabElement.getAttribute('data-bs-target') || 
                        tabElement.getAttribute('href');
        
        if (targetId) {
            console.log(`Switching to tab: ${targetId}`);
            // Additional tab switch logic if needed
        }
    }

    handleCopyToClipboard(element) {
        const textToCopy = element.dataset.copyText || 
                          element.previousElementSibling?.textContent ||
                          element.textContent;
        
        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                this.manager.uiNotifications?.showSuccess('Copied to clipboard');
            }).catch(err => {
                console.error('Copy failed:', err);
                this.manager.uiNotifications?.showError('Failed to copy to clipboard');
            });
        }
    }

    initializeTooltip(element) {
        if (!element.dataset.tooltipInitialized) {
            new bootstrap.Tooltip(element);
            element.dataset.tooltipInitialized = 'true';
        }
    }

    triggerConfigurationChange(type, data) {
        // Emit custom event for configuration changes
        const event = new CustomEvent('emotionalConfigChange', {
            detail: { type, data, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
        
        // Auto-save if enabled
        if (this.manager.autoSaveEnabled) {
            clearTimeout(this.manager.autoSaveTimer);
            this.manager.autoSaveTimer = setTimeout(() => {
                this.manager.saveConfiguration(true); // Silent save
            }, this.manager.autoSaveDelay || 2000);
        }
    }

    /**
     * Event listener management
     */
    addEventHandler(target, eventType, handler, options = {}) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) {
            console.warn('Event target not found:', target);
            return;
        }

        const key = `${eventType}-${Date.now()}-${Math.random()}`;
        
        element.addEventListener(eventType, handler, options);
        
        this.eventListeners.set(key, {
            element,
            eventType,
            handler,
            options
        });

        return key;
    }

    removeEventHandler(key) {
        const listener = this.eventListeners.get(key);
        if (listener) {
            listener.element.removeEventListener(
                listener.eventType, 
                listener.handler, 
                listener.options
            );
            this.eventListeners.delete(key);
            return true;
        }
        return false;
    }

    /**
     * Cleanup all event listeners
     */
    cleanup() {
        for (const [key, listener] of this.eventListeners) {
            listener.element.removeEventListener(
                listener.eventType, 
                listener.handler, 
                listener.options
            );
        }
        this.eventListeners.clear();
        this.initialized = false;
        console.log('Event handlers cleaned up');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigEventHandler;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigEventHandler = EmotionalConfigEventHandler;
}