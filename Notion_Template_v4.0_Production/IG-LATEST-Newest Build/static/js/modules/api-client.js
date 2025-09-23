/**
 * Estate Planning v4.0 - API Client Module
 * Handles all HTTP communications with the Flask backend
 */

class EmotionalConfigAPIClient {
    constructor() {
        this.baseUrl = '/api/emotional-config';
        this.csrfToken = null;
    }

    /**
     * Initialize CSRF token
     */
    async initializeCSRF() {
        try {
            const response = await fetch('/api/get-csrf-token', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.csrfToken = data.csrf_token;
            return this.csrfToken;
        } catch (error) {
            console.error('CSRF token initialization failed:', error);
            throw error;
        }
    }

    /**
     * Get request headers with CSRF token
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        if (this.csrfToken) {
            headers['X-CSRFToken'] = this.csrfToken;
        }

        return headers;
    }

    /**
     * Load current emotional configuration from server
     */
    async loadConfiguration() {
        try {
            const response = await fetch(`${this.baseUrl}/load`, {
                method: 'GET',
                credentials: 'same-origin',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Failed to load configuration: HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Configuration load failed:', error);
            throw error;
        }
    }

    /**
     * Save emotional configuration to server
     */
    async saveConfiguration(configData) {
        try {
            const response = await fetch(`${this.baseUrl}/save`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: this.getHeaders(),
                body: JSON.stringify(configData)
            });

            if (!response.ok) {
                throw new Error(`Failed to save configuration: HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Configuration save failed:', error);
            throw error;
        }
    }

    /**
     * Reset configuration to defaults
     */
    async resetToDefaults() {
        try {
            const response = await fetch(`${this.baseUrl}/reset`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Failed to reset configuration: HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Configuration reset failed:', error);
            throw error;
        }
    }

    /**
     * Preview configuration changes
     */
    async previewChanges(configData) {
        try {
            const response = await fetch(`${this.baseUrl}/preview`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: this.getHeaders(),
                body: JSON.stringify(configData)
            });

            if (!response.ok) {
                throw new Error(`Failed to preview changes: HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Configuration preview failed:', error);
            throw error;
        }
    }

    /**
     * Generate test assets with current configuration
     */
    async generateTestAssets(configData) {
        try {
            const response = await fetch(`${this.baseUrl}/generate-test`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: this.getHeaders(),
                body: JSON.stringify(configData)
            });

            if (!response.ok) {
                throw new Error(`Failed to generate test assets: HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Test asset generation failed:', error);
            throw error;
        }
    }

    /**
     * Health check endpoint
     */
    async healthCheck() {
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json'
                }
            });

            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    /**
     * Get system status
     */
    async getSystemStatus() {
        try {
            const response = await fetch('/api/status', {
                method: 'GET',
                credentials: 'same-origin',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Failed to get system status: HTTP ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('System status check failed:', error);
            throw error;
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigAPIClient;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigAPIClient = EmotionalConfigAPIClient;
}