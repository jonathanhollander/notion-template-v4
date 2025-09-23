/**
 * Estate Planning v4.0 - DOM Renderer Module
 * Handles all HTML generation and DOM manipulation
 */

class EmotionalConfigDOMRenderer {
    constructor() {
        this.templates = {
            toneCard: this.getToneCardTemplate(),
            styleCategory: this.getStyleCategoryTemplate(),
            keywordTag: this.getKeywordTagTemplate(),
            styleElement: this.getStyleElementTemplate(),
            previewSection: this.getPreviewSectionTemplate()
        };
    }

    /**
     * Render complete emotional tone card
     */
    renderToneCard(toneName, toneData, intensity = 0.8) {
        const card = document.createElement('div');
        card.className = 'tone-card';
        card.dataset.tone = toneName;
        
        card.innerHTML = `
            <div class="tone-header">
                <div class="tone-name">${toneData.name || toneName}</div>
                <div class="intensity-value">${Math.round(intensity * 100)}%</div>
            </div>
            <p class="text-muted mb-3">${toneData.description || 'No description available'}</p>
            
            <div class="intensity-slider mb-3">
                <label class="form-label">Intensity Level</label>
                <input type="range" class="form-range intensity-range" 
                       min="0" max="1" step="0.05" value="${intensity}"
                       data-tone="${toneName}">
            </div>
            
            <div class="keywords-section mb-3">
                <label class="form-label">Keywords</label>
                <div class="keywords-container" data-tone="${toneName}">
                    ${this.renderKeywords(toneData.keywords || [])}
                </div>
                <div class="add-input-group">
                    <input type="text" class="form-control form-control-sm add-keyword-input" 
                           placeholder="Add new keyword..." data-tone="${toneName}">
                    <button class="btn btn-outline-primary btn-sm add-keyword-btn" data-tone="${toneName}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }

    /**
     * Render keyword tags
     */
    renderKeywords(keywords) {
        if (!Array.isArray(keywords)) return '';
        
        return keywords.map(keyword => `
            <span class="keyword-tag">
                ${this.escapeHtml(keyword)}
                <span class="remove-keyword" data-keyword="${this.escapeHtml(keyword)}">×</span>
            </span>
        `).join('');
    }

    /**
     * Render style category section
     */
    renderStyleCategory(categoryName, elements, description = '') {
        const container = document.createElement('div');
        container.className = 'style-category';
        container.dataset.category = categoryName;
        
        container.innerHTML = `
            <div class="style-category-header">
                <h6>${this.formatCategoryName(categoryName)}</h6>
                <small class="text-muted">${description}</small>
            </div>
            <div class="style-elements-container" data-category="${categoryName}">
                ${this.renderStyleElements(elements)}
            </div>
            <div class="add-input-group">
                <input type="text" class="form-control form-control-sm add-element-input" 
                       placeholder="Add new ${categoryName}..." data-category="${categoryName}">
                <button class="btn btn-outline-secondary btn-sm add-element-btn" data-category="${categoryName}">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
        `;
        
        return container;
    }

    /**
     * Render style elements
     */
    renderStyleElements(elements) {
        if (!Array.isArray(elements)) return '';
        
        return elements.map(element => `
            <span class="style-element">
                ${this.escapeHtml(element)}
                <span class="remove-element" data-element="${this.escapeHtml(element)}">×</span>
            </span>
        `).join('');
    }

    /**
     * Render preview section with generated content
     */
    renderPreviewSection(previewData) {
        const container = document.createElement('div');
        container.className = 'preview-section';
        
        if (!previewData || previewData.length === 0) {
            container.innerHTML = `
                <div class="preview-area">
                    <p class="text-muted">
                        <i class="fas fa-info-circle me-2"></i>
                        Click "Preview Changes" to see how your configuration affects prompt generation
                    </p>
                </div>
            `;
            return container;
        }

        container.innerHTML = `
            <h5>Generated Preview</h5>
            <div class="preview-content">
                ${previewData.map(item => this.renderPreviewItem(item)).join('')}
            </div>
        `;
        
        return container;
    }

    /**
     * Render individual preview item
     */
    renderPreviewItem(item) {
        return `
            <div class="preview-item mb-3 p-3 border rounded">
                <h6 class="preview-title">${this.escapeHtml(item.title || 'Untitled')}</h6>
                <div class="preview-prompt">
                    <strong>Generated Prompt:</strong>
                    <pre class="preview-text">${this.escapeHtml(item.prompt || 'No prompt generated')}</pre>
                </div>
                ${item.emotional_context ? `
                    <div class="preview-emotional-context mt-2">
                        <strong>Emotional Context:</strong>
                        <small class="text-muted d-block">${this.escapeHtml(item.emotional_context)}</small>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Render loading spinner
     */
    renderLoadingSpinner(message = 'Loading...') {
        return `
            <div class="loading-spinner d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
    }

    /**
     * Render progress bar
     */
    renderProgressBar(percentage, label = '') {
        const width = Math.max(0, Math.min(100, percentage));
        return `
            <div class="progress mb-2">
                <div class="progress-bar preview-progress-bar" role="progressbar" 
                     style="width: ${width}%" aria-valuenow="${width}" 
                     aria-valuemin="0" aria-valuemax="100">
                    ${width > 15 ? `${Math.round(width)}%` : ''}
                </div>
            </div>
            ${label ? `<small class="text-muted">${this.escapeHtml(label)}</small>` : ''}
        `;
    }

    /**
     * Update tone card intensity display
     */
    updateToneIntensity(toneName, intensity) {
        const card = document.querySelector(`.tone-card[data-tone="${toneName}"]`);
        if (!card) return;

        const valueDisplay = card.querySelector('.intensity-value');
        const slider = card.querySelector('.intensity-range');
        
        if (valueDisplay) {
            valueDisplay.textContent = `${Math.round(intensity * 100)}%`;
        }
        
        if (slider) {
            slider.value = intensity;
        }
    }

    /**
     * Add keyword to tone card
     */
    addKeywordToTone(toneName, keyword) {
        const container = document.querySelector(`.keywords-container[data-tone="${toneName}"]`);
        if (!container) return false;

        // Check if keyword already exists
        const existing = container.querySelector(`[data-keyword="${this.escapeHtml(keyword)}"]`);
        if (existing) return false;

        const keywordElement = document.createElement('span');
        keywordElement.className = 'keyword-tag';
        keywordElement.innerHTML = `
            ${this.escapeHtml(keyword)}
            <span class="remove-keyword" data-keyword="${this.escapeHtml(keyword)}">×</span>
        `;
        
        container.appendChild(keywordElement);
        return true;
    }

    /**
     * Remove keyword from tone card
     */
    removeKeywordFromTone(toneName, keyword) {
        const container = document.querySelector(`.keywords-container[data-tone="${toneName}"]`);
        if (!container) return false;

        const keywordElement = container.querySelector(`[data-keyword="${this.escapeHtml(keyword)}"]`);
        if (keywordElement) {
            keywordElement.closest('.keyword-tag').remove();
            return true;
        }
        return false;
    }

    /**
     * Add style element to category
     */
    addStyleElement(categoryName, element) {
        const container = document.querySelector(`.style-elements-container[data-category="${categoryName}"]`);
        if (!container) return false;

        // Check if element already exists
        const existing = container.querySelector(`[data-element="${this.escapeHtml(element)}"]`);
        if (existing) return false;

        const elementSpan = document.createElement('span');
        elementSpan.className = 'style-element';
        elementSpan.innerHTML = `
            ${this.escapeHtml(element)}
            <span class="remove-element" data-element="${this.escapeHtml(element)}">×</span>
        `;
        
        container.appendChild(elementSpan);
        return true;
    }

    /**
     * Remove style element from category
     */
    removeStyleElement(categoryName, element) {
        const container = document.querySelector(`.style-elements-container[data-category="${categoryName}"]`);
        if (!container) return false;

        const elementSpan = container.querySelector(`[data-element="${this.escapeHtml(element)}"]`);
        if (elementSpan) {
            elementSpan.closest('.style-element').remove();
            return true;
        }
        return false;
    }

    /**
     * Clear all content from container
     */
    clearContainer(selector) {
        const container = document.querySelector(selector);
        if (container) {
            container.innerHTML = '';
            return true;
        }
        return false;
    }

    /**
     * Show/hide loading state on element
     */
    toggleLoadingState(element, isLoading, message = 'Loading...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;

        if (isLoading) {
            element.classList.add('generating');
            const loadingHtml = this.renderLoadingSpinner(message);
            element.insertAdjacentHTML('beforeend', loadingHtml);
        } else {
            element.classList.remove('generating');
            const spinner = element.querySelector('.loading-spinner');
            if (spinner) spinner.remove();
        }
    }

    /**
     * Template methods
     */
    getToneCardTemplate() {
        return `
            <div class="tone-card" data-tone="{toneName}">
                <div class="tone-header">
                    <div class="tone-name">{toneDisplayName}</div>
                    <div class="intensity-value">{intensityPercent}%</div>
                </div>
                <p class="text-muted mb-3">{description}</p>
                <div class="intensity-slider mb-3">
                    <label class="form-label">Intensity Level</label>
                    <input type="range" class="form-range intensity-range" 
                           min="0" max="1" step="0.05" value="{intensity}"
                           data-tone="{toneName}">
                </div>
                <div class="keywords-section mb-3">
                    <label class="form-label">Keywords</label>
                    <div class="keywords-container" data-tone="{toneName}">
                        {keywordsList}
                    </div>
                    <div class="add-input-group">
                        <input type="text" class="form-control form-control-sm add-keyword-input" 
                               placeholder="Add new keyword..." data-tone="{toneName}">
                        <button class="btn btn-outline-primary btn-sm add-keyword-btn" data-tone="{toneName}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getStyleCategoryTemplate() {
        return `
            <div class="style-category" data-category="{categoryName}">
                <div class="style-category-header">
                    <h6>{categoryDisplayName}</h6>
                    <small class="text-muted">{description}</small>
                </div>
                <div class="style-elements-container" data-category="{categoryName}">
                    {elementsList}
                </div>
                <div class="add-input-group">
                    <input type="text" class="form-control form-control-sm add-element-input" 
                           placeholder="Add new {categoryName}..." data-category="{categoryName}">
                    <button class="btn btn-outline-secondary btn-sm add-element-btn" data-category="{categoryName}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `;
    }

    getKeywordTagTemplate() {
        return `<span class="keyword-tag">{keyword}<span class="remove-keyword" data-keyword="{keyword}">×</span></span>`;
    }

    getStyleElementTemplate() {
        return `<span class="style-element">{element}<span class="remove-element" data-element="{element}">×</span></span>`;
    }

    getPreviewSectionTemplate() {
        return `
            <div class="preview-section">
                <h5>Generated Preview</h5>
                <div class="preview-content">
                    {previewContent}
                </div>
            </div>
        `;
    }

    /**
     * Utility methods
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }

    formatCategoryName(name) {
        return name.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Animation utilities
     */
    fadeIn(element, duration = 300) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;

        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = performance.now();
        
        function animate(timestamp) {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    fadeOut(element, duration = 300) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;

        let start = performance.now();
        const initialOpacity = parseFloat(getComputedStyle(element).opacity) || 1;
        
        function animate(timestamp) {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = initialOpacity * (1 - progress);
            
            if (progress >= 1) {
                element.style.display = 'none';
            } else {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigDOMRenderer;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigDOMRenderer = EmotionalConfigDOMRenderer;
}