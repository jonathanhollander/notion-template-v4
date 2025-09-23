/**
 * Estate Planning v4.0 - Data Validator Module
 * Handles all input validation, sanitization, and data integrity checks
 */

class EmotionalConfigDataValidator {
    constructor() {
        this.validationRules = {
            keyword: {
                minLength: 1,
                maxLength: 50,
                pattern: /^[a-zA-Z0-9\s\-_.,;:!?'"()[\]{}]+$/,
                description: 'Keywords must be 1-50 characters and contain only letters, numbers, spaces, and basic punctuation'
            },
            styleElement: {
                minLength: 1,
                maxLength: 100,
                pattern: /^[a-zA-Z0-9\s\-_.,;:!?'"()[\]{}]+$/,
                description: 'Style elements must be 1-100 characters and contain only letters, numbers, spaces, and basic punctuation'
            },
            intensity: {
                min: 0,
                max: 1,
                step: 0.01,
                description: 'Intensity must be a number between 0 and 1'
            },
            toneName: {
                minLength: 1,
                maxLength: 50,
                pattern: /^[A-Z_]+$/,
                description: 'Tone names must be uppercase letters and underscores only'
            },
            categoryName: {
                minLength: 1,
                maxLength: 30,
                pattern: /^[a-z_]+$/,
                description: 'Category names must be lowercase letters and underscores only'
            }
        };

        this.sanitizationConfig = {
            allowedTags: [], // No HTML tags allowed
            allowedAttributes: {},
            stripEmptyTags: true,
            maxLength: 1000 // Global max length
        };
    }

    /**
     * Validate and sanitize keyword input
     */
    validateKeyword(keyword) {
        if (typeof keyword !== 'string') return false;
        
        const sanitized = this.sanitizeInput(keyword);
        const rule = this.validationRules.keyword;
        
        return sanitized.length >= rule.minLength && 
               sanitized.length <= rule.maxLength &&
               rule.pattern.test(sanitized);
    }

    /**
     * Validate and sanitize style element input
     */
    validateStyleElement(element) {
        if (typeof element !== 'string') return false;
        
        const sanitized = this.sanitizeInput(element);
        const rule = this.validationRules.styleElement;
        
        return sanitized.length >= rule.minLength && 
               sanitized.length <= rule.maxLength &&
               rule.pattern.test(sanitized);
    }

    /**
     * Validate intensity value
     */
    validateIntensity(intensity) {
        const num = parseFloat(intensity);
        if (isNaN(num)) return false;
        
        const rule = this.validationRules.intensity;
        return num >= rule.min && num <= rule.max;
    }

    /**
     * Validate tone name format
     */
    validateToneName(toneName) {
        if (typeof toneName !== 'string') return false;
        
        const rule = this.validationRules.toneName;
        return toneName.length >= rule.minLength && 
               toneName.length <= rule.maxLength &&
               rule.pattern.test(toneName);
    }

    /**
     * Validate category name format
     */
    validateCategoryName(categoryName) {
        if (typeof categoryName !== 'string') return false;
        
        const rule = this.validationRules.categoryName;
        return categoryName.length >= rule.minLength && 
               categoryName.length <= rule.maxLength &&
               rule.pattern.test(categoryName);
    }

    /**
     * Sanitize general text input
     */
    sanitizeInput(input) {
        if (typeof input !== 'string') return '';
        
        let sanitized = input;
        
        // Remove or encode potentially dangerous characters
        sanitized = sanitized
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
        
        // Remove control characters except tabs, newlines, and carriage returns
        sanitized = sanitized.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
        
        // Trim whitespace
        sanitized = sanitized.trim();
        
        // Enforce max length
        if (sanitized.length > this.sanitizationConfig.maxLength) {
            sanitized = sanitized.substring(0, this.sanitizationConfig.maxLength);
        }
        
        return sanitized;
    }

    /**
     * Deep sanitize object data
     */
    sanitizeObject(obj) {
        if (!obj || typeof obj !== 'object') return obj;
        
        if (Array.isArray(obj)) {
            return obj.map(item => this.sanitizeObject(item));
        }
        
        const sanitized = {};
        for (const [key, value] of Object.entries(obj)) {
            const cleanKey = this.sanitizeInput(key);
            
            if (typeof value === 'string') {
                sanitized[cleanKey] = this.sanitizeInput(value);
            } else if (typeof value === 'number') {
                sanitized[cleanKey] = this.sanitizeNumber(value);
            } else if (typeof value === 'boolean') {
                sanitized[cleanKey] = Boolean(value);
            } else if (typeof value === 'object') {
                sanitized[cleanKey] = this.sanitizeObject(value);
            }
        }
        
        return sanitized;
    }

    /**
     * Sanitize and validate numeric input
     */
    sanitizeNumber(input) {
        const num = parseFloat(input);
        if (isNaN(num)) return 0;
        
        // Prevent infinities
        if (!isFinite(num)) return 0;
        
        return num;
    }

    /**
     * Validate complete emotional configuration object
     */
    validateConfiguration(config) {
        const errors = [];
        const warnings = [];
        
        if (!config || typeof config !== 'object') {
            errors.push('Configuration must be an object');
            return { valid: false, errors, warnings };
        }

        // Validate emotional tones
        if (config.emotional_tones) {
            if (typeof config.emotional_tones !== 'object') {
                errors.push('emotional_tones must be an object');
            } else {
                for (const [toneName, toneData] of Object.entries(config.emotional_tones)) {
                    const toneErrors = this.validateTone(toneName, toneData);
                    errors.push(...toneErrors.map(err => `Tone "${toneName}": ${err}`));
                }
            }
        }

        // Validate style elements
        if (config.style_elements) {
            if (typeof config.style_elements !== 'object') {
                errors.push('style_elements must be an object');
            } else {
                for (const [categoryName, elements] of Object.entries(config.style_elements)) {
                    const categoryErrors = this.validateStyleCategory(categoryName, elements);
                    errors.push(...categoryErrors.map(err => `Category "${categoryName}": ${err}`));
                }
            }
        }

        // Check for required fields
        const requiredTones = ['WARM_WELCOME', 'TRUSTED_GUIDE', 'FAMILY_HERITAGE', 'SECURE_PROTECTION', 
                              'PEACEFUL_TRANSITION', 'LIVING_CONTINUITY', 'TECH_BRIDGE'];
        
        if (config.emotional_tones) {
            for (const requiredTone of requiredTones) {
                if (!config.emotional_tones[requiredTone]) {
                    warnings.push(`Missing recommended tone: ${requiredTone}`);
                }
            }
        }

        const requiredCategories = ['materials', 'lighting', 'colors', 'textures', 'objects', 'composition'];
        
        if (config.style_elements) {
            for (const requiredCategory of requiredCategories) {
                if (!config.style_elements[requiredCategory] || !Array.isArray(config.style_elements[requiredCategory])) {
                    warnings.push(`Missing or invalid style category: ${requiredCategory}`);
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors,
            warnings
        };
    }

    /**
     * Validate individual tone configuration
     */
    validateTone(toneName, toneData) {
        const errors = [];
        
        if (!this.validateToneName(toneName)) {
            errors.push('Invalid tone name format');
        }
        
        if (!toneData || typeof toneData !== 'object') {
            errors.push('Tone data must be an object');
            return errors;
        }

        // Validate intensity
        if (toneData.intensity !== undefined) {
            if (!this.validateIntensity(toneData.intensity)) {
                errors.push('Invalid intensity value');
            }
        }

        // Validate keywords
        if (toneData.keywords) {
            if (!Array.isArray(toneData.keywords)) {
                errors.push('Keywords must be an array');
            } else {
                toneData.keywords.forEach((keyword, index) => {
                    if (!this.validateKeyword(keyword)) {
                        errors.push(`Invalid keyword at index ${index}: ${keyword}`);
                    }
                });
            }
        }

        // Validate name
        if (toneData.name && typeof toneData.name !== 'string') {
            errors.push('Tone name must be a string');
        }

        // Validate description
        if (toneData.description && typeof toneData.description !== 'string') {
            errors.push('Tone description must be a string');
        }

        return errors;
    }

    /**
     * Validate style category
     */
    validateStyleCategory(categoryName, elements) {
        const errors = [];
        
        if (!this.validateCategoryName(categoryName)) {
            errors.push('Invalid category name format');
        }
        
        if (!Array.isArray(elements)) {
            errors.push('Style elements must be an array');
            return errors;
        }

        elements.forEach((element, index) => {
            if (!this.validateStyleElement(element)) {
                errors.push(`Invalid style element at index ${index}: ${element}`);
            }
        });

        return errors;
    }

    /**
     * Check for potential security issues
     */
    performSecurityScan(data) {
        const issues = [];
        const dataStr = JSON.stringify(data);
        
        // Check for potential script injection
        const scriptPatterns = [
            /<script/i,
            /javascript:/i,
            /vbscript:/i,
            /onload=/i,
            /onerror=/i,
            /onclick=/i,
            /eval\(/i,
            /expression\(/i,
            /document\.cookie/i,
            /document\.write/i
        ];

        scriptPatterns.forEach(pattern => {
            if (pattern.test(dataStr)) {
                issues.push(`Potential script injection detected: ${pattern.source}`);
            }
        });

        // Check for suspicious URLs
        const urlPatterns = [
            /https?:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)/i,
            /ftp:/i,
            /file:/i,
            /data:/i
        ];

        urlPatterns.forEach(pattern => {
            if (pattern.test(dataStr)) {
                issues.push(`Suspicious URL pattern detected: ${pattern.source}`);
            }
        });

        // Check for excessive length (potential DoS)
        if (dataStr.length > 100000) {
            issues.push('Data size exceeds safe limits');
        }

        return issues;
    }

    /**
     * Validate file upload data
     */
    validateFileData(fileData) {
        const errors = [];
        
        if (!fileData) {
            errors.push('No file data provided');
            return { valid: false, errors };
        }

        // Check file size (in bytes)
        if (fileData.size > 10 * 1024 * 1024) { // 10MB limit
            errors.push('File size exceeds 10MB limit');
        }

        // Check file type
        const allowedTypes = ['application/json', 'text/plain', 'text/yaml'];
        if (!allowedTypes.includes(fileData.type)) {
            errors.push(`Invalid file type: ${fileData.type}. Allowed types: ${allowedTypes.join(', ')}`);
        }

        // Check filename
        if (fileData.name) {
            const filename = fileData.name;
            if (!/^[a-zA-Z0-9._-]+$/.test(filename)) {
                errors.push('Filename contains invalid characters');
            }
            
            if (filename.length > 255) {
                errors.push('Filename too long');
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate API response data
     */
    validateAPIResponse(response) {
        const errors = [];
        
        if (!response) {
            errors.push('No response data');
            return { valid: false, errors };
        }

        // Check for error field
        if (response.error) {
            errors.push(`API error: ${response.error}`);
        }

        // Validate success field
        if (typeof response.success !== 'boolean') {
            errors.push('Missing or invalid success field');
        }

        // Check response size
        const responseStr = JSON.stringify(response);
        if (responseStr.length > 1000000) { // 1MB limit
            errors.push('Response size too large');
        }

        return {
            valid: errors.length === 0,
            errors,
            data: response
        };
    }

    /**
     * Get validation rule for specific field type
     */
    getValidationRule(fieldType) {
        return this.validationRules[fieldType] || null;
    }

    /**
     * Get error message for validation failure
     */
    getErrorMessage(fieldType, value) {
        const rule = this.validationRules[fieldType];
        if (!rule) return 'Unknown validation error';

        if (typeof value === 'string') {
            if (value.length < rule.minLength) {
                return `Minimum length is ${rule.minLength} characters`;
            }
            if (value.length > rule.maxLength) {
                return `Maximum length is ${rule.maxLength} characters`;
            }
            if (rule.pattern && !rule.pattern.test(value)) {
                return rule.description || 'Invalid format';
            }
        }

        if (typeof value === 'number') {
            if (rule.min !== undefined && value < rule.min) {
                return `Minimum value is ${rule.min}`;
            }
            if (rule.max !== undefined && value > rule.max) {
                return `Maximum value is ${rule.max}`;
            }
        }

        return rule.description || 'Invalid input';
    }

    /**
     * Check if input needs sanitization
     */
    needsSanitization(input) {
        if (typeof input !== 'string') return false;
        
        const sanitized = this.sanitizeInput(input);
        return input !== sanitized;
    }

    /**
     * Batch validate multiple inputs
     */
    validateBatch(inputs) {
        const results = {};
        
        for (const [key, { value, type }] of Object.entries(inputs)) {
            switch (type) {
                case 'keyword':
                    results[key] = {
                        valid: this.validateKeyword(value),
                        sanitized: this.sanitizeInput(value),
                        error: this.validateKeyword(value) ? null : this.getErrorMessage('keyword', value)
                    };
                    break;
                case 'styleElement':
                    results[key] = {
                        valid: this.validateStyleElement(value),
                        sanitized: this.sanitizeInput(value),
                        error: this.validateStyleElement(value) ? null : this.getErrorMessage('styleElement', value)
                    };
                    break;
                case 'intensity':
                    results[key] = {
                        valid: this.validateIntensity(value),
                        sanitized: this.sanitizeNumber(value),
                        error: this.validateIntensity(value) ? null : this.getErrorMessage('intensity', value)
                    };
                    break;
                default:
                    results[key] = {
                        valid: true,
                        sanitized: this.sanitizeInput(value),
                        error: null
                    };
            }
        }
        
        return results;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigDataValidator;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigDataValidator = EmotionalConfigDataValidator;
}