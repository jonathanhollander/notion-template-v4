/**
 * Estate Planning v4.0 - Emotional Config Manager (Main Controller)
 * Orchestrates all modules to provide the complete emotional intelligence interface
 */

class EmotionalConfigManager {
    constructor() {
        // Module instances
        this.apiClient = null;
        this.domRenderer = null;
        this.eventHandler = null;
        this.uiNotifications = null;
        this.dataValidator = null;
        
        // State management
        this.currentConfig = null;
        this.originalConfig = null;
        this.hasUnsavedChanges = false;
        this.isLoading = false;
        this.currentOperation = null;
        
        // Auto-save configuration
        this.autoSaveEnabled = false;
        this.autoSaveDelay = 2000; // 2 seconds
        this.autoSaveTimer = null;
        
        // DOM selectors
        this.selectors = {
            tonesContainer: '#emotional-tones-container',
            styleContainer: '#style-elements-container',
            previewContainer: '#preview-container',
            loadBtn: '#load-config-btn',
            saveBtn: '#save-config-btn',
            resetBtn: '#reset-defaults-btn',
            previewBtn: '#preview-changes-btn',
            generateBtn: '#generate-test-btn'
        };
        
        this.initialized = false;
    }

    /**
     * Initialize the complete emotional config system
     */
    async initialize() {
        if (this.initialized) {
            console.warn('EmotionalConfigManager already initialized');
            return;
        }

        try {
            console.log('Initializing EmotionalConfigManager...');
            
            // Initialize all modules
            await this.initializeModules();
            
            // Load initial configuration
            await this.loadInitialConfiguration();
            
            // Set up auto-save
            this.setupAutoSave();
            
            // Mark as initialized
            this.initialized = true;
            
            console.log('EmotionalConfigManager initialized successfully');
            this.uiNotifications.showSuccess('Emotional Intelligence Configuration loaded successfully');
            
        } catch (error) {
            console.error('Failed to initialize EmotionalConfigManager:', error);
            this.uiNotifications?.showError(`Initialization failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Initialize all module instances
     */
    async initializeModules() {
        console.log('Initializing modules...');
        
        // Initialize in dependency order
        this.dataValidator = new EmotionalConfigDataValidator();
        this.apiClient = new EmotionalConfigAPIClient();
        this.uiNotifications = new EmotionalConfigUINotifications();
        this.domRenderer = new EmotionalConfigDOMRenderer();
        this.eventHandler = new EmotionalConfigEventHandler(this);
        
        // Initialize modules that need setup
        this.uiNotifications.initialize();
        this.eventHandler.initialize();
        
        // Initialize CSRF token for API
        await this.apiClient.initializeCSRF();
        
        console.log('All modules initialized');
    }

    /**
     * Load initial configuration from server or defaults
     */
    async loadInitialConfiguration() {
        console.log('Loading initial configuration...');
        
        try {
            const response = await this.apiClient.loadConfiguration();
            this.currentConfig = response.configuration || this.getDefaultConfiguration();
            this.originalConfig = JSON.parse(JSON.stringify(this.currentConfig));
            
            // Render the configuration in the UI
            this.renderConfiguration();
            
        } catch (error) {
            console.warn('Failed to load configuration from server, using defaults:', error);
            this.currentConfig = this.getDefaultConfiguration();
            this.originalConfig = JSON.parse(JSON.stringify(this.currentConfig));
            this.renderConfiguration();
        }
    }

    /**
     * Render the current configuration in the UI
     */
    renderConfiguration() {
        console.log('Rendering configuration...');
        
        try {
            // Clear existing content
            this.domRenderer.clearContainer(this.selectors.tonesContainer);
            this.domRenderer.clearContainer(this.selectors.styleContainer);
            
            // Render emotional tones
            this.renderEmotionalTones();
            
            // Render style elements
            this.renderStyleElements();
            
            // Update UI state
            this.updateUIState();
            
        } catch (error) {
            console.error('Failed to render configuration:', error);
            this.uiNotifications.showError('Failed to render configuration interface');
        }
    }

    /**
     * Render emotional tones section
     */
    renderEmotionalTones() {
        const container = document.querySelector(this.selectors.tonesContainer);
        if (!container || !this.currentConfig.emotional_tones) return;

        for (const [toneName, toneData] of Object.entries(this.currentConfig.emotional_tones)) {
            const toneCard = this.domRenderer.renderToneCard(toneName, toneData, toneData.intensity || 0.8);
            container.appendChild(toneCard);
        }
    }

    /**
     * Render style elements section
     */
    renderStyleElements() {
        const container = document.querySelector(this.selectors.styleContainer);
        if (!container || !this.currentConfig.style_elements) return;

        for (const [categoryName, elements] of Object.entries(this.currentConfig.style_elements)) {
            const categoryCard = this.domRenderer.renderStyleCategory(categoryName, elements);
            container.appendChild(categoryCard);
        }
    }

    /**
     * Load configuration from server
     */
    async loadConfiguration() {
        if (this.isLoading) {
            this.uiNotifications.showWarning('Another operation is in progress');
            return;
        }

        try {
            this.setLoadingState(true, 'Loading configuration...');
            
            const response = await this.apiClient.loadConfiguration();
            
            if (response.success) {
                this.currentConfig = response.configuration;
                this.originalConfig = JSON.parse(JSON.stringify(this.currentConfig));
                this.renderConfiguration();
                this.hasUnsavedChanges = false;
                
                this.uiNotifications.showSuccess('Configuration loaded successfully');
            } else {
                throw new Error(response.error || 'Failed to load configuration');
            }
            
        } catch (error) {
            console.error('Load configuration failed:', error);
            this.uiNotifications.showError(`Failed to load configuration: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Save current configuration to server
     */
    async saveConfiguration(silent = false) {
        if (this.isLoading) {
            this.uiNotifications.showWarning('Another operation is in progress');
            return;
        }

        try {
            this.setLoadingState(true, 'Saving configuration...');
            
            // Validate configuration before saving
            const validation = this.dataValidator.validateConfiguration(this.currentConfig);
            
            if (!validation.valid) {
                throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
            }
            
            if (validation.warnings.length > 0) {
                console.warn('Configuration warnings:', validation.warnings);
            }
            
            // Sanitize configuration
            const sanitizedConfig = this.dataValidator.sanitizeObject(this.currentConfig);
            
            const response = await this.apiClient.saveConfiguration(sanitizedConfig);
            
            if (response.success) {
                this.originalConfig = JSON.parse(JSON.stringify(this.currentConfig));
                this.hasUnsavedChanges = false;
                
                if (!silent) {
                    this.uiNotifications.showSuccess('Configuration saved successfully');
                }
            } else {
                throw new Error(response.error || 'Failed to save configuration');
            }
            
        } catch (error) {
            console.error('Save configuration failed:', error);
            this.uiNotifications.showError(`Failed to save configuration: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Reset configuration to defaults
     */
    async resetToDefaults() {
        if (this.isLoading) {
            this.uiNotifications.showWarning('Another operation is in progress');
            return;
        }

        try {
            this.setLoadingState(true, 'Resetting to defaults...');
            
            const response = await this.apiClient.resetToDefaults();
            
            if (response.success) {
                this.currentConfig = response.configuration || this.getDefaultConfiguration();
                this.originalConfig = JSON.parse(JSON.stringify(this.currentConfig));
                this.renderConfiguration();
                this.hasUnsavedChanges = false;
                
                this.uiNotifications.showSuccess('Configuration reset to defaults');
            } else {
                throw new Error(response.error || 'Failed to reset configuration');
            }
            
        } catch (error) {
            console.error('Reset configuration failed:', error);
            this.uiNotifications.showError(`Failed to reset configuration: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Preview configuration changes
     */
    async previewChanges() {
        if (this.isLoading) {
            this.uiNotifications.showWarning('Another operation is in progress');
            return;
        }

        try {
            this.setLoadingState(true, 'Generating preview...');
            
            // Validate configuration before preview
            const validation = this.dataValidator.validateConfiguration(this.currentConfig);
            
            if (!validation.valid) {
                throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
            }
            
            const response = await this.apiClient.previewChanges(this.currentConfig);
            
            if (response.success) {
                this.renderPreview(response.preview_data);
                this.uiNotifications.showSuccess('Preview generated successfully');
            } else {
                throw new Error(response.error || 'Failed to generate preview');
            }
            
        } catch (error) {
            console.error('Preview generation failed:', error);
            this.uiNotifications.showError(`Failed to generate preview: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Generate test assets with current configuration
     */
    async generateTestAssets() {
        if (this.isLoading) {
            this.uiNotifications.showWarning('Another operation is in progress');
            return;
        }

        // Show confirmation dialog first
        const confirmed = await new Promise((resolve) => {
            this.uiNotifications.showConfirm(
                'Generate Test Assets',
                'This will generate test assets using your current configuration. This process may take a few minutes and will incur API costs. Continue?',
                () => resolve(true),
                () => resolve(false)
            );
        });

        if (!confirmed) return;

        try {
            this.setLoadingState(true, 'Generating test assets...');
            
            const response = await this.apiClient.generateTestAssets(this.currentConfig);
            
            if (response.success) {
                this.uiNotifications.showSuccess(`Test assets generated successfully. ${response.assets_count} assets created.`);
                
                if (response.preview_urls && response.preview_urls.length > 0) {
                    this.renderAssetPreview(response.preview_urls);
                }
            } else {
                throw new Error(response.error || 'Failed to generate test assets');
            }
            
        } catch (error) {
            console.error('Test asset generation failed:', error);
            this.uiNotifications.showError(`Failed to generate test assets: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Render preview data in the preview container
     */
    renderPreview(previewData) {
        const container = document.querySelector(this.selectors.previewContainer);
        if (!container) return;

        container.innerHTML = '';
        const previewSection = this.domRenderer.renderPreviewSection(previewData);
        container.appendChild(previewSection);
    }

    /**
     * Render asset preview images
     */
    renderAssetPreview(previewUrls) {
        const container = document.querySelector(this.selectors.previewContainer);
        if (!container || !previewUrls.length) return;

        const previewSection = document.createElement('div');
        previewSection.className = 'asset-preview-section mt-4';
        previewSection.innerHTML = `
            <h5>Generated Test Assets</h5>
            <div class="row">
                ${previewUrls.map(url => `
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <img src="${url}" class="card-img-top" alt="Generated Asset" style="max-height: 200px; object-fit: cover;">
                            <div class="card-body">
                                <button class="btn btn-sm btn-outline-primary copy-btn" data-copy-text="${url}">
                                    Copy URL
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.appendChild(previewSection);
    }

    /**
     * Set loading state for UI
     */
    setLoadingState(isLoading, message = 'Loading...') {
        this.isLoading = isLoading;
        this.currentOperation = isLoading ? message : null;
        
        // Update button states
        const buttons = document.querySelectorAll(`
            ${this.selectors.loadBtn}, 
            ${this.selectors.saveBtn}, 
            ${this.selectors.resetBtn}, 
            ${this.selectors.previewBtn}, 
            ${this.selectors.generateBtn}
        `);
        
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = isLoading;
                if (isLoading) {
                    btn.dataset.originalText = btn.textContent;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>' + message;
                } else {
                    btn.innerHTML = btn.dataset.originalText || btn.textContent;
                }
            }
        });
    }

    /**
     * Update UI state based on current configuration
     */
    updateUIState() {
        // Update save button based on unsaved changes
        const saveBtn = document.querySelector(this.selectors.saveBtn);
        if (saveBtn) {
            saveBtn.classList.toggle('btn-warning', this.hasUnsavedChanges);
            saveBtn.classList.toggle('btn-primary', !this.hasUnsavedChanges);
        }
        
        // Update page title if there are unsaved changes
        if (this.hasUnsavedChanges) {
            document.title = '* Emotional Configuration - Estate Planning v4.0';
        } else {
            document.title = 'Emotional Configuration - Estate Planning v4.0';
        }
    }

    /**
     * Setup auto-save functionality
     */
    setupAutoSave() {
        // Listen for configuration changes
        document.addEventListener('emotionalConfigChange', (event) => {
            this.hasUnsavedChanges = true;
            this.updateUIState();
            
            // Trigger auto-save if enabled
            if (this.autoSaveEnabled) {
                clearTimeout(this.autoSaveTimer);
                this.autoSaveTimer = setTimeout(() => {
                    this.saveConfiguration(true); // Silent save
                }, this.autoSaveDelay);
            }
        });

        // Save on page unload if there are unsaved changes
        window.addEventListener('beforeunload', (event) => {
            if (this.hasUnsavedChanges) {
                event.preventDefault();
                event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return event.returnValue;
            }
        });
    }

    /**
     * Get default configuration structure
     */
    getDefaultConfiguration() {
        return {
            emotional_tones: {
                WARM_WELCOME: {
                    name: 'Warm Welcome',
                    description: 'Entry points - welcoming and accessible tone',
                    keywords: ['welcoming', 'inviting', 'accessible', 'comfortable', 'open'],
                    intensity: 0.8
                },
                TRUSTED_GUIDE: {
                    name: 'Trusted Guide',
                    description: 'Executor sections - reliable and professional guidance',
                    keywords: ['reliable', 'professional', 'authoritative', 'trustworthy', 'competent'],
                    intensity: 0.9
                },
                FAMILY_HERITAGE: {
                    name: 'Family Heritage',
                    description: 'Family sections - warmth and generational connection',
                    keywords: ['familial', 'generational', 'legacy', 'heritage', 'connection'],
                    intensity: 0.85
                },
                SECURE_PROTECTION: {
                    name: 'Secure Protection',
                    description: 'Financial/legal - safety and security emphasis',
                    keywords: ['secure', 'protected', 'safe', 'reliable', 'fortress-like'],
                    intensity: 0.95
                },
                PEACEFUL_TRANSITION: {
                    name: 'Peaceful Transition',
                    description: 'Difficult topics - gentle and comforting approach',
                    keywords: ['gentle', 'peaceful', 'comforting', 'serene', 'graceful'],
                    intensity: 0.7
                },
                LIVING_CONTINUITY: {
                    name: 'Living Continuity',
                    description: 'Legacy sections - life continuing and enduring impact',
                    keywords: ['continuing', 'enduring', 'lasting', 'perpetual', 'ongoing'],
                    intensity: 0.8
                },
                TECH_BRIDGE: {
                    name: 'Tech Bridge',
                    description: 'Digital sections - bridging traditional and digital worlds',
                    keywords: ['bridging', 'connecting', 'modern', 'accessible', 'integrative'],
                    intensity: 0.75
                }
            },
            style_elements: {
                materials: ['warm wood grain', 'brushed metal accents', 'soft leather textures', 'natural stone surfaces'],
                lighting: ['gentle morning light', 'golden hour warmth', 'soft ambient glow', 'filtered natural light'],
                colors: ['estate blues', 'heritage golds', 'comfort whites', 'wisdom grays'],
                textures: ['leather-bound surfaces', 'hand-crafted details', 'time-worn elegance', 'smooth stone finish'],
                objects: ['family heirlooms', 'trusted documents', 'connecting bridges', 'protective shields'],
                composition: ['centered balance', 'flowing connection', 'protective embrace', 'guiding pathway']
            }
        };
    }

    /**
     * Export current configuration
     */
    exportConfiguration() {
        const dataStr = JSON.stringify(this.currentConfig, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `emotional-config-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        this.uiNotifications.showSuccess('Configuration exported successfully');
    }

    /**
     * Import configuration from file
     */
    async importConfiguration(file) {
        try {
            // Validate file
            const fileValidation = this.dataValidator.validateFileData(file);
            if (!fileValidation.valid) {
                throw new Error(fileValidation.errors.join(', '));
            }
            
            // Read file content
            const fileContent = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = e => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsText(file);
            });
            
            // Parse and validate configuration
            const importedConfig = JSON.parse(fileContent);
            const validation = this.dataValidator.validateConfiguration(importedConfig);
            
            if (!validation.valid) {
                throw new Error(`Invalid configuration file: ${validation.errors.join(', ')}`);
            }
            
            // Apply imported configuration
            this.currentConfig = importedConfig;
            this.renderConfiguration();
            this.hasUnsavedChanges = true;
            this.updateUIState();
            
            this.uiNotifications.showSuccess('Configuration imported successfully');
            
            if (validation.warnings.length > 0) {
                this.uiNotifications.showWarning(`Import warnings: ${validation.warnings.join(', ')}`);
            }
            
        } catch (error) {
            console.error('Import failed:', error);
            this.uiNotifications.showError(`Import failed: ${error.message}`);
        }
    }

    /**
     * Enable or disable auto-save
     */
    setAutoSave(enabled) {
        this.autoSaveEnabled = enabled;
        if (enabled) {
            this.uiNotifications.showInfo('Auto-save enabled');
        } else {
            this.uiNotifications.showInfo('Auto-save disabled');
            clearTimeout(this.autoSaveTimer);
        }
    }

    /**
     * Get system health status
     */
    async getHealthStatus() {
        try {
            const isHealthy = await this.apiClient.healthCheck();
            const status = await this.apiClient.getSystemStatus();
            
            return {
                healthy: isHealthy,
                ...status
            };
        } catch (error) {
            console.error('Health check failed:', error);
            return { healthy: false, error: error.message };
        }
    }

    /**
     * Cleanup resources and event listeners
     */
    cleanup() {
        // Clear timers
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Cleanup modules
        if (this.eventHandler) {
            this.eventHandler.cleanup();
        }
        
        if (this.uiNotifications) {
            this.uiNotifications.cleanup();
        }
        
        // Reset state
        this.initialized = false;
        this.currentConfig = null;
        this.originalConfig = null;
        this.hasUnsavedChanges = false;
        this.isLoading = false;
        this.currentOperation = null;
        
        console.log('EmotionalConfigManager cleaned up');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigManager;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigManager = EmotionalConfigManager;
}