/**
 * Estate Planning v4.0 - UI Notifications Module
 * Handles all user notifications, status messages, and feedback
 */

class EmotionalConfigUINotifications {
    constructor() {
        this.container = null;
        this.defaultDuration = 5000; // 5 seconds
        this.maxNotifications = 5;
        this.notificationQueue = [];
        this.activeNotifications = new Map();
        this.initialized = false;
    }

    /**
     * Initialize notification system
     */
    initialize() {
        if (this.initialized) {
            console.warn('UI Notifications already initialized');
            return;
        }

        this.createNotificationContainer();
        this.initialized = true;
        console.log('UI Notifications initialized');
    }

    /**
     * Create notification container if it doesn't exist
     */
    createNotificationContainer() {
        // Check if container already exists
        this.container = document.getElementById('notification-container');
        
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        }
    }

    /**
     * Show success notification
     */
    showSuccess(message, options = {}) {
        return this.show(message, 'success', {
            icon: 'fas fa-check-circle',
            duration: options.duration || this.defaultDuration,
            ...options
        });
    }

    /**
     * Show error notification
     */
    showError(message, options = {}) {
        return this.show(message, 'error', {
            icon: 'fas fa-exclamation-circle',
            duration: options.duration || (this.defaultDuration * 2), // Errors stay longer
            persistent: options.persistent || false,
            ...options
        });
    }

    /**
     * Show warning notification
     */
    showWarning(message, options = {}) {
        return this.show(message, 'warning', {
            icon: 'fas fa-exclamation-triangle',
            duration: options.duration || this.defaultDuration,
            ...options
        });
    }

    /**
     * Show info notification
     */
    showInfo(message, options = {}) {
        return this.show(message, 'info', {
            icon: 'fas fa-info-circle',
            duration: options.duration || this.defaultDuration,
            ...options
        });
    }

    /**
     * Show loading notification
     */
    showLoading(message, options = {}) {
        return this.show(message, 'loading', {
            icon: 'fas fa-spinner fa-spin',
            persistent: true, // Loading notifications don't auto-dismiss
            showProgress: options.showProgress || false,
            ...options
        });
    }

    /**
     * Main notification display method
     */
    show(message, type = 'info', options = {}) {
        if (!this.initialized) {
            this.initialize();
        }

        const notification = this.createNotification(message, type, options);
        const notificationId = this.generateId();
        
        notification.dataset.notificationId = notificationId;
        
        // Remove oldest notification if at max capacity
        if (this.activeNotifications.size >= this.maxNotifications) {
            const oldestId = this.activeNotifications.keys().next().value;
            this.dismiss(oldestId);
        }

        // Add to container
        this.container.appendChild(notification);
        this.activeNotifications.set(notificationId, notification);

        // Trigger enter animation
        requestAnimationFrame(() => {
            notification.classList.add('notification-enter');
        });

        // Auto-dismiss if not persistent
        if (!options.persistent && options.duration > 0) {
            setTimeout(() => {
                this.dismiss(notificationId);
            }, options.duration);
        }

        return notificationId;
    }

    /**
     * Create notification DOM element
     */
    createNotification(message, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            pointer-events: auto;
            margin-bottom: 10px;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transform: translateX(100%);
            transition: all 0.3s ease;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            line-height: 1.4;
            min-width: 300px;
        `;

        // Set colors based on type
        const colors = this.getTypeColors(type);
        notification.style.backgroundColor = colors.background;
        notification.style.color = colors.text;
        notification.style.border = `1px solid ${colors.border}`;

        // Create icon
        const iconElement = document.createElement('div');
        iconElement.className = 'notification-icon';
        iconElement.style.cssText = `
            flex-shrink: 0;
            margin-top: 2px;
        `;
        if (options.icon) {
            iconElement.innerHTML = `<i class="${options.icon}"></i>`;
        }

        // Create content
        const contentElement = document.createElement('div');
        contentElement.className = 'notification-content';
        contentElement.style.cssText = `
            flex: 1;
            min-width: 0;
        `;

        // Create message
        const messageElement = document.createElement('div');
        messageElement.className = 'notification-message';
        messageElement.innerHTML = this.escapeHtml(message);

        contentElement.appendChild(messageElement);

        // Add progress bar if requested
        if (options.showProgress) {
            const progressBar = this.createProgressBar();
            contentElement.appendChild(progressBar);
        }

        // Create close button (unless persistent)
        let closeButton = null;
        if (!options.hideClose) {
            closeButton = document.createElement('button');
            closeButton.className = 'notification-close';
            closeButton.innerHTML = '×';
            closeButton.style.cssText = `
                background: none;
                border: none;
                font-size: 18px;
                line-height: 1;
                cursor: pointer;
                padding: 0;
                margin-left: auto;
                opacity: 0.7;
                flex-shrink: 0;
                color: inherit;
            `;
            closeButton.onmouseover = () => closeButton.style.opacity = '1';
            closeButton.onmouseout = () => closeButton.style.opacity = '0.7';
        }

        // Assemble notification
        notification.appendChild(iconElement);
        notification.appendChild(contentElement);
        if (closeButton) {
            notification.appendChild(closeButton);
            closeButton.onclick = () => {
                const id = notification.dataset.notificationId;
                this.dismiss(id);
            };
        }

        return notification;
    }

    /**
     * Create progress bar element
     */
    createProgressBar() {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'notification-progress';
        progressContainer.style.cssText = `
            margin-top: 8px;
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
        `;

        const progressBar = document.createElement('div');
        progressBar.className = 'notification-progress-bar';
        progressBar.style.cssText = `
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s ease;
        `;

        progressContainer.appendChild(progressBar);
        return progressContainer;
    }

    /**
     * Update progress of a loading notification
     */
    updateProgress(notificationId, percentage, message = null) {
        const notification = this.activeNotifications.get(notificationId);
        if (!notification) return false;

        const progressBar = notification.querySelector('.notification-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
        }

        if (message) {
            const messageElement = notification.querySelector('.notification-message');
            if (messageElement) {
                messageElement.innerHTML = this.escapeHtml(message);
            }
        }

        return true;
    }

    /**
     * Dismiss notification
     */
    dismiss(notificationId) {
        const notification = this.activeNotifications.get(notificationId);
        if (!notification) return false;

        // Start exit animation
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';

        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.activeNotifications.delete(notificationId);
        }, 300);

        return true;
    }

    /**
     * Dismiss all notifications
     */
    dismissAll() {
        const ids = Array.from(this.activeNotifications.keys());
        ids.forEach(id => this.dismiss(id));
    }

    /**
     * Show status message in fixed status bar
     */
    showStatus(message, type = 'info', duration = 3000) {
        let statusElement = document.getElementById('config-status');
        
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'config-status';
            statusElement.className = 'config-status';
            document.body.appendChild(statusElement);
        }

        statusElement.textContent = message;
        statusElement.className = `config-status ${type}`;
        statusElement.style.display = 'block';

        if (duration > 0) {
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, duration);
        }
    }

    /**
     * Show toast message (simple, unobtrusive notification)
     */
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 14px;
            z-index: 10000;
            transition: transform 0.3s ease;
            max-width: 80vw;
            text-align: center;
        `;

        toast.textContent = message;
        document.body.appendChild(toast);

        // Show animation
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(-50%) translateY(0)';
        });

        // Hide and remove
        setTimeout(() => {
            toast.style.transform = 'translateX(-50%) translateY(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    /**
     * Show modal alert
     */
    showAlert(title, message, type = 'info', actions = null) {
        const modalId = this.generateId();
        const titleId = `${modalId}-title`;
        const bodyId = `${modalId}-body`;
        
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', titleId);
        modal.setAttribute('aria-describedby', bodyId);
        modal.setAttribute('aria-hidden', 'true');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="${titleId}">${this.escapeHtml(title)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close dialog"></button>
                    </div>
                    <div class="modal-body" id="${bodyId}">
                        <div class="d-flex align-items-start">
                            <div class="me-3" aria-hidden="true">
                                <i class="${this.getTypeIcon(type)} fs-3 text-${this.getTypeBootstrapClass(type)}"></i>
                            </div>
                            <div class="flex-grow-1">
                                ${this.escapeHtml(message)}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        ${actions ? actions : '<button type="button" class="btn btn-primary" data-bs-dismiss="modal">OK</button>'}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });

        bootstrapModal.show();
        return bootstrapModal;
    }

    /**
     * Show confirmation dialog
     */
    showConfirm(title, message, onConfirm, onCancel = null) {
        const actions = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="cancel-btn">Cancel</button>
            <button type="button" class="btn btn-danger" id="confirm-btn">Confirm</button>
        `;

        const modal = this.showAlert(title, message, 'warning', actions);
        
        document.getElementById('confirm-btn').onclick = () => {
            modal.hide();
            if (onConfirm) onConfirm();
        };

        document.getElementById('cancel-btn').onclick = () => {
            modal.hide();
            if (onCancel) onCancel();
        };

        return modal;
    }

    /**
     * Utility methods
     */
    getTypeColors(type) {
        const colors = {
            success: {
                background: '#d4edda',
                text: '#155724',
                border: '#c3e6cb'
            },
            error: {
                background: '#f8d7da',
                text: '#721c24',
                border: '#f5c6cb'
            },
            warning: {
                background: '#fff3cd',
                text: '#856404',
                border: '#ffeaa7'
            },
            info: {
                background: '#cce7ff',
                text: '#004085',
                border: '#abdaff'
            },
            loading: {
                background: '#e2e3e5',
                text: '#383d41',
                border: '#d6d8db'
            }
        };

        return colors[type] || colors.info;
    }

    getTypeIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
            loading: 'fas fa-spinner fa-spin'
        };

        return icons[type] || icons.info;
    }

    getTypeBootstrapClass(type) {
        const classes = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info',
            loading: 'secondary'
        };

        return classes[type] || classes.info;
    }

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

    generateId() {
        return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get notification count
     */
    getActiveCount() {
        return this.activeNotifications.size;
    }

    /**
     * Check if notification exists
     */
    exists(notificationId) {
        return this.activeNotifications.has(notificationId);
    }

    /**
     * Cleanup all notifications and event listeners
     */
    cleanup() {
        this.dismissAll();
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        this.container = null;
        this.initialized = false;
        console.log('UI Notifications cleaned up');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmotionalConfigUINotifications;
}

// Global registration for browser usage
if (typeof window !== 'undefined') {
    window.EmotionalConfigUINotifications = EmotionalConfigUINotifications;
}