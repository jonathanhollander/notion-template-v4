let currentEvaluationIndex = 0;
let totalEvaluations = 0;
let sessionActive = false;
let sessionId = null;
let csrfToken = null;

// Sanitization helper functions
function sanitizeInput(input) {
    if (typeof input !== 'string') return '';
    return DOMPurify.sanitize(input, {
        ALLOWED_TAGS: [],  // No HTML tags allowed
        ALLOWED_ATTR: []   // No attributes allowed
    });
}

function sanitizeHTML(html) {
    return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['p', 'strong', 'em', 'br'],
        ALLOWED_ATTR: []
    });
}

// Loading state management
function setLoading(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
        // Save and replace text with loading indicator
        element.dataset.originalText = element.textContent;
        element.innerHTML = '<span class="spinner"></span> Loading...';
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        // Restore original text
        if (element.dataset.originalText) {
            element.textContent = element.dataset.originalText;
            delete element.dataset.originalText;
        }
    }
}

// Toast notifications
function showToast(message, type = 'success') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = sanitizeInput(message);
    
    toastContainer.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// CSRF Token Management
async function getCSRFToken() {
    try {
        const response = await fetch('/api/get-csrf-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken()
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        if (result.success) {
            sessionId = result.session_id;
            csrfToken = result.csrf_token;
            return true;
        } else {
            console.error('Failed to get CSRF token:', result.error);
            return false;
        }
    } catch (error) {
        console.error('Error getting CSRF token:', error);
        return false;
    }
}

function getAPIToken() {
    // Always return the internal token - no user input needed
    return 'estate-planning-review-2024';
}

async function getCsrfToken() {
    try {
        const response = await fetch('/api/get-csrf-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken()
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.session_id && data.csrf_token) {
            sessionId = data.session_id;
            csrfToken = data.csrf_token;
            
            // Store in sessionStorage
            sessionStorage.setItem('session_id', sessionId);
            sessionStorage.setItem('csrf_token', csrfToken);
            
            return true;
        } else {
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        console.error('Failed to get CSRF token:', error);
        showToast('Failed to get security token. Please check your API token.', 'error');
        return false;
    }
}

async function startSession() {
    const reviewerName = sanitizeInput(document.getElementById('reviewer-name').value) || 'Anonymous';
    const startButton = document.querySelector('button[onclick="startSession()"]');
    
    setLoading(startButton, true);
    
    // First get CSRF token
    if (!await getCsrfToken()) {
        showToast('Failed to get security token. Please check your API token.', 'error');
        setLoading(startButton, false);
        return;
    }
    
    try {
        const response = await fetch('/api/start-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken(),
                'X-Session-ID': sessionId,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({reviewer_name: reviewerName})
        });
        
        const result = await response.json();
        if (result.success) {
            sessionActive = true;
            document.getElementById('session-status').textContent = `Active (${sanitizeInput(reviewerName)})`;
            
            // Enhanced visual feedback and workflow progression
            showToast('Review session started successfully!', 'success');
            
            // Add progress indication
            const authSection = document.querySelector('.auth-section');
            const progressIndicator = document.createElement('div');
            progressIndicator.className = 'workflow-progress';
            progressIndicator.innerHTML = `
                <div class="progress-step completed">
                    <span class="step-number">1</span>
                    <span class="step-text">Session Started ✓</span>
                </div>
                <div class="progress-step active">
                    <span class="step-number">2</span>
                    <span class="step-text">Loading Evaluations...</span>
                </div>
                <div class="progress-step">
                    <span class="step-number">3</span>
                    <span class="step-text">Begin Review</span>
                </div>
            `;
            authSection.appendChild(progressIndicator);
            
            // Auto-advance to next step after a brief delay
            setTimeout(() => {
                showToast('Auto-loading evaluations...', 'info');
                loadEvaluations();
            }, 1500);
            
        } else {
            showToast('Failed to start session: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error starting session:', error);
        showToast('Error starting session: ' + error.message, 'error');
    } finally {
        setLoading(startButton, false);
    }
}

async function loadEvaluations() {
    if (!sessionActive) {
        showToast('Please start a review session first', 'warning');
        return;
    }
    
    const loadButton = document.querySelector('button[onclick="loadEvaluations()"]');
    setLoading(loadButton, true);
    
    try {
        const response = await fetch('/api/load-evaluations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken(),
                'X-Session-ID': sessionId,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({file_path: 'quality_evaluation_results.json'})
        });
        
        const result = await response.json();
        if (result.success) {
            totalEvaluations = result.evaluations_loaded;
            document.getElementById('evaluations-count').textContent = totalEvaluations;
            document.getElementById('export-btn').disabled = false;
            
            // Initialize progress display with enhanced visualization
            const currentDecisions = parseInt(document.getElementById('decisions-count').textContent) || 0;
            updateProgressDisplay(currentDecisions, totalEvaluations);
            
            // Load first evaluation
            await loadEvaluation(0);
            
            // Update workflow progress indicator
            const progressIndicator = document.querySelector('.workflow-progress');
            if (progressIndicator) {
                const steps = progressIndicator.querySelectorAll('.progress-step');
                if (steps.length >= 3) {
                    // Mark step 2 as completed
                    steps[1].classList.remove('active');
                    steps[1].classList.add('completed');
                    steps[1].querySelector('.step-text').textContent = 'Evaluations Loaded ✓';
                    
                    // Activate step 3
                    steps[2].classList.add('active');
                    steps[2].querySelector('.step-text').textContent = 'Review Ready - Begin!';
                }
            }
            
            // Smooth transition between states
            const preReviewMessage = document.getElementById('pre-review-message');
            const evaluationDisplay = document.getElementById('evaluation-display');
            
            // Hide pre-review message with animation
            preReviewMessage.classList.add('hidden');
            
            // Show evaluation display with animation after brief delay
            setTimeout(() => {
                preReviewMessage.style.display = 'none';
                evaluationDisplay.style.display = 'block';
                // Trigger reflow for animation
                evaluationDisplay.offsetHeight;
                evaluationDisplay.classList.add('visible');
            }, 300);
            
            showToast(`Loaded ${totalEvaluations} evaluations successfully!`, 'success');
        } else {
            showToast(`Failed to load evaluations: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error loading evaluations:', error);
        showToast('Error loading evaluations: ' + error.message, 'error');
    } finally {
        setLoading(loadButton, false);
    }
}

async function loadEvaluation(index) {
    try {
        const response = await fetch(`/api/get-evaluation/${index}`, {
            headers: {
                'X-API-TOKEN': getAPIToken()
            }
        });
        const result = await response.json();
        
        if (result.success) {
            const evaluation = result.evaluation;
            
            // Update header
            document.getElementById('eval-title').textContent = sanitizeInput(evaluation.page_title);
            document.getElementById('eval-category').textContent = sanitizeInput(evaluation.page_category);
            document.getElementById('eval-type').textContent = sanitizeInput(evaluation.asset_type);
            
            // Update prompts container
            const container = document.getElementById('prompts-container');
            // Safe DOM manipulation - remove all children
            while (container.firstChild) {
                container.removeChild(container.firstChild);
            }
            
            // Update selection dropdown
            const select = document.getElementById('selected-prompt');
            // Safe DOM manipulation - clear and add default option
            while (select.firstChild) {
                select.removeChild(select.firstChild);
            }
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a prompt...';
            select.appendChild(defaultOption);
            
            evaluation.prompts.forEach((prompt, idx) => {
                // Create prompt display
                const promptDiv = document.createElement('div');
                promptDiv.className = 'prompt-container';
                
                // Create safe DOM elements instead of innerHTML
                const promptHeader = document.createElement('div');
                promptHeader.className = 'prompt-header';
                
                const modelSource = document.createElement('div');
                modelSource.className = 'model-source';
                modelSource.textContent = sanitizeInput(prompt.model_source);
                
                const scoreBadge = document.createElement('span');
                scoreBadge.className = 'score-badge';
                scoreBadge.textContent = prompt.weighted_score.toFixed(2) + '/10';
                
                promptHeader.appendChild(modelSource);
                promptHeader.appendChild(scoreBadge);
                
                const promptText = document.createElement('div');
                promptText.className = 'prompt-text';
                promptText.textContent = sanitizeInput(prompt.text);
                
                const scoreDetails = document.createElement('div');
                scoreDetails.className = 'score-details';
                scoreDetails.innerHTML = `<span><strong>Overall:</strong> ${prompt.overall_score.toFixed(1)}</span><span><strong>Weighted:</strong> ${prompt.weighted_score.toFixed(2)}</span>`;
                
                promptDiv.appendChild(promptHeader);
                promptDiv.appendChild(promptText);
                promptDiv.appendChild(scoreDetails);
                
                if (evaluation.winner && prompt.id === evaluation.winner.id) {
                    promptDiv.classList.add('ai-winner');  // Use new enhanced class
                    const badge = document.createElement('span');
                    badge.style.background = '#28a745';
                    badge.style.color = 'white';
                    badge.style.padding = '4px 8px';
                    badge.style.borderRadius = '4px';
                    badge.style.fontSize = '12px';
                    badge.textContent = 'AI WINNER';
                    promptDiv.querySelector('.prompt-header').appendChild(badge);
                }
                
                container.appendChild(promptDiv);
                
                // Add to selection dropdown
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = `${sanitizeInput(prompt.model_source)} (${prompt.weighted_score.toFixed(2)})`;
                select.appendChild(option);
            });
            
            currentEvaluationIndex = index;
        } else {
            showToast(`Error loading evaluation: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error loading evaluation:', error);
        showToast('Error loading evaluation: ' + error.message, 'error');
    }
}

async function makeDecision() {
    const selectedPromptId = sanitizeInput(document.getElementById('selected-prompt').value);
    const reasoning = sanitizeInput(document.getElementById('decision-reasoning').value);
    const modifications = sanitizeInput(document.getElementById('custom-modifications').value);
    
    if (!selectedPromptId) {
        showToast('Please select a prompt first', 'warning');
        return;
    }
    
    if (!reasoning.trim()) {
        showToast('Please provide reasoning for your decision', 'warning');
        return;
    }
    
    const decisionButton = document.querySelector('button[onclick="makeDecision()"]');
    setLoading(decisionButton, true);
    
    try {
        const response = await fetch('/api/make-decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken(),
                'X-Session-ID': sessionId,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                page_title: document.getElementById('eval-title').textContent,
                page_category: document.getElementById('eval-category').textContent,
                asset_type: document.getElementById('eval-type').textContent,
                selected_prompt_id: selectedPromptId,
                selected_model: document.getElementById('selected-prompt').selectedOptions[0].textContent.split(' (')[0],
                reasoning: reasoning,
                custom_modifications: modifications
            })
        });
        
        const result = await response.json();
        if (result.success) {
            // Update progress with enhanced display
            document.getElementById('decisions-count').textContent = result.total_decisions;
            updateProgressDisplay(result.total_decisions, totalEvaluations);
            
            // Clear form
            document.getElementById('selected-prompt').value = '';
            document.getElementById('decision-reasoning').value = '';
            document.getElementById('custom-modifications').value = '';
            
            showToast('Decision recorded successfully!', 'success');
        } else {
            showToast(`Error recording decision: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error making decision:', error);
        showToast('Error recording decision: ' + error.message, 'error');
    } finally {
        setLoading(decisionButton, false);
    }
}

async function nextEvaluation() {
    if (currentEvaluationIndex < totalEvaluations - 1) {
        await loadEvaluation(currentEvaluationIndex + 1);
    } else {
        showToast('No more evaluations to review!', 'warning');
    }
}

async function exportDecisions() {
    const exportButton = document.getElementById('export-btn');
    setLoading(exportButton, true);
    
    try {
        const response = await fetch('/api/export-decisions', {
            headers: {
                'X-API-TOKEN': getAPIToken()
            }
        });
        const result = await response.json();
        
        if (result.success) {
            showToast(`Exported ${result.total_decisions} decisions to ${result.file_path}`, 'success');
        } else {
            showToast('Error exporting decisions', 'error');
        }
    } catch (error) {
        console.error('Error exporting decisions:', error);
        showToast('Error exporting decisions: ' + error.message, 'error');
    } finally {
        setLoading(exportButton, false);
    }
}

// Enhanced progress display with color coding
function updateProgressDisplay(completed, total) {
    const percentage = total > 0 ? (completed / total) * 100 : 0;
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    // Update progress bar width
    progressFill.style.width = `${percentage}%`;
    
    // Color coding based on completion
    if (percentage === 100) {
        progressFill.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
    } else if (percentage >= 75) {
        progressFill.style.background = 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)';
    } else if (percentage >= 50) {
        progressFill.style.background = 'linear-gradient(135deg, #ffc107 0%, #e0a800 100%)';
    } else {
        progressFill.style.background = 'linear-gradient(135deg, #8B4513 0%, #D2691E 100%)';
    }
    
    // Enhanced text display with "X of Y decisions made"
    progressText.innerHTML = `
        <strong>${percentage.toFixed(1)}% Complete</strong>
        <small style="display: block; margin-top: 4px; opacity: 0.9;">
            ${completed} of ${total} decisions made
        </small>
    `;
}

// Keyboard shortcuts for efficiency
document.addEventListener('keydown', function(event) {
    // Skip if user is typing in a text field
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT') {
        return;
    }
    
    // Ctrl/Cmd + key combinations
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;
    
    if (isCtrlOrCmd) {
        switch(event.key) {
            case 's': // Ctrl+S - Save decision
                event.preventDefault();
                if (document.getElementById('selected-prompt').value) {
                    makeDecision();
                }
                break;
            case 'ArrowRight': // Ctrl+Right - Next evaluation
                event.preventDefault();
                nextEvaluation();
                break;
            case 'ArrowLeft': // Ctrl+Left - Previous evaluation
                event.preventDefault();
                if (currentEvaluationIndex > 0) {
                    loadEvaluation(currentEvaluationIndex - 1);
                }
                break;
            case 'e': // Ctrl+E - Export decisions
                event.preventDefault();
                if (!document.getElementById('export-btn').disabled) {
                    exportDecisions();
                }
                break;
            case 'l': // Ctrl+L - Load evaluations
                event.preventDefault();
                if (sessionActive) {
                    loadEvaluations();
                }
                break;
        }
    } else {
        // Single key shortcuts (when not in input fields)
        switch(event.key) {
            case '1': // Select prompt 1
            case '2': // Select prompt 2
            case '3': // Select prompt 3
                const selectElement = document.getElementById('selected-prompt');
                const optionIndex = parseInt(event.key);
                if (selectElement.options[optionIndex]) {
                    selectElement.selectedIndex = optionIndex;
                    // Focus on reasoning field after selection
                    document.getElementById('decision-reasoning').focus();
                }
                break;
            case 'n': // Next evaluation
                nextEvaluation();
                break;
            case 'p': // Previous evaluation
                if (currentEvaluationIndex > 0) {
                    loadEvaluation(currentEvaluationIndex - 1);
                }
                break;
            case 'r': // Focus on reasoning field
                document.getElementById('decision-reasoning').focus();
                break;
            case 'm': // Focus on modifications field
                document.getElementById('custom-modifications').focus();
                break;
            case '?': // Show keyboard shortcuts help
                showKeyboardShortcutsHelp();
                break;
        }
    }
});

// Function to show keyboard shortcuts help
function showKeyboardShortcutsHelp() {
    const shortcuts = `
Keyboard Shortcuts:
━━━━━━━━━━━━━━━━━━
Navigation:
• n / →: Next evaluation
• p / ←: Previous evaluation
• Ctrl+→: Next evaluation
• Ctrl+←: Previous evaluation

Selection:
• 1-3: Select prompt by number
• r: Focus reasoning field
• m: Focus modifications field

Actions:
• Ctrl+S: Save decision
• Ctrl+L: Load evaluations
• Ctrl+E: Export decisions
• ?: Show this help
    `;
    alert(shortcuts);
}

// Auto-refresh progress every 30 seconds
setInterval(async () => {
    if (sessionActive) {
        try {
            const response = await fetch('/api/get-progress', {
                headers: {
                    'X-API-TOKEN': getAPIToken()
                }
            });
            const progress = await response.json();
            
            document.getElementById('decisions-count').textContent = progress.decisions_made;
            updateProgressDisplay(progress.decisions_made, totalEvaluations);
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }
}, 30000);

// ============================================
// WebSocket Integration for Real-Time Updates
// ============================================

// WebSocket connection
let socket = null;

// Initialize WebSocket connection
function initWebSocket() {
    // Check if Socket.IO is available
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to WebSocket');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from WebSocket');
            updateConnectionStatus(false);
        });
        
        socket.on('generation_status', function(data) {
            updateGenerationStatus(data);
        });
        
        socket.on('prompt_generation', function(data) {
            updatePromptGeneration(data);
        });
        
        socket.on('image_generation', function(data) {
            updateImageGeneration(data);
        });
        
        socket.on('circuit_breaker_status', function(data) {
            updateCircuitBreakerStatus(data);
        });
        
        socket.on('generation_error', function(data) {
            handleGenerationError(data);
        });
        
        socket.on('log_message', function(data) {
            appendLogMessage(data);
        });
    } else {
        console.warn('Socket.IO not available. Real-time updates disabled.');
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('websocket-status');
    if (indicator) {
        indicator.className = connected ? 'status-connected' : 'status-disconnected';
        indicator.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
    }
}

// Update generation status display
function updateGenerationStatus(data) {
    const panel = document.getElementById('generation-status-panel');
    if (panel) {
        panel.style.display = 'block';
    }
    
    // Update current phase
    const phaseElement = document.getElementById('current-phase');
    if (phaseElement) {
        phaseElement.textContent = data.phase || 'Unknown';
    }
    
    // Update progress bar
    const progressElement = document.getElementById('generation-progress');
    if (progressElement && data.progress !== undefined) {
        progressElement.style.width = data.progress + '%';
        progressElement.setAttribute('aria-valuenow', data.progress);
    }
    
    // Update metrics if provided
    if (data.prompts_count !== undefined) {
        const promptsElement = document.getElementById('prompts-count');
        if (promptsElement) promptsElement.textContent = data.prompts_count;
    }
    
    if (data.images_count !== undefined) {
        const imagesElement = document.getElementById('images-count');
        if (imagesElement) imagesElement.textContent = data.images_count;
    }
    
    if (data.cost !== undefined) {
        const costElement = document.getElementById('generation-cost');
        if (costElement) costElement.textContent = '$' + data.cost.toFixed(2);
    }
}

// Append log message to the log stream (Enhanced for full-width log system)
function appendLogMessage(data) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    
    // Remove placeholder if it exists
    const placeholder = logContainer.querySelector('.log-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry log-' + (data.level || 'info') + ' new-entry';
    
    const timestamp = new Date(data.timestamp || Date.now()).toLocaleTimeString();
    logEntry.innerHTML = '<span class="log-timestamp">[' + timestamp + ']</span> ' +
                         '<span class="log-message">' + sanitizeHTML(data.message) + '</span>';
    
    logContainer.appendChild(logEntry);
    
    // Auto-scroll to bottom if enabled
    if (isAutoScrollEnabled()) {
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    // Update log count
    updateLogCount();
    
    // Remove new-entry class after animation
    setTimeout(() => {
        logEntry.classList.remove('new-entry');
    }, 300);
    
    // Limit log entries to prevent memory issues
    while (logContainer.children.length > 1000) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// Start test generation
async function startTestGeneration() {
    try {
        // Show status panel
        const panel = document.getElementById('generation-status-panel');
        if (panel) {
            panel.style.display = 'block';
        }
        
        // Get CSRF token if needed
        if (!csrfToken || !sessionId) {
            await getCsrfToken();
        }
        
        const response = await fetch('/api/start-generation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-TOKEN': getAPIToken(),
                'X-Session-ID': sessionId,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                mode: 'sample',
                test_pages: 3
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Test generation started (3 images)', 'success');
            appendLogMessage({
                level: 'info',
                message: '🚀 Starting sample generation (3 images)',
                timestamp: new Date().toISOString()
            });
        } else {
            throw new Error(data.error || 'Failed to start generation');
        }
        
    } catch (error) {
        showToast('Failed to start generation: ' + error.message, 'error');
        console.error('Generation start error:', error);
    }
}

// ============================================
// FULL-WIDTH LOG SYSTEM ENHANCEMENTS
// ============================================

// Auto-scroll state management
let autoScrollEnabled = true;
let logCount = 0;

// Check if auto-scroll is enabled
function isAutoScrollEnabled() {
    return autoScrollEnabled;
}

// Toggle auto-scroll functionality
function toggleLogAutoScroll() {
    autoScrollEnabled = !autoScrollEnabled;
    const btn = document.getElementById('autoscroll-btn');
    const logContainer = document.getElementById('log-container');
    
    if (btn) {
        btn.textContent = `📜 Auto-scroll: ${autoScrollEnabled ? 'ON' : 'OFF'}`;
        btn.title = `Auto-scroll is ${autoScrollEnabled ? 'enabled' : 'disabled'}`;
    }
    
    if (logContainer) {
        if (autoScrollEnabled) {
            logContainer.classList.add('auto-scroll');
            logContainer.scrollTop = logContainer.scrollHeight;
        } else {
            logContainer.classList.remove('auto-scroll');
        }
    }
}

// Clear all log entries
function clearLogs() {
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
        // Add placeholder back
        logContainer.innerHTML = `
            <div class="log-placeholder">
                <p>🗑️ Logs cleared</p>
                <p>New system events will appear here in real-time.</p>
            </div>
        `;
        logCount = 0;
        updateLogCount();
        
        // Show brief confirmation
        showToast('Log cleared successfully', 'info');
    }
}

// Export logs to downloadable file
function exportLogs() {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    
    const logEntries = logContainer.querySelectorAll('.log-entry');
    if (logEntries.length === 0) {
        showToast('No logs to export', 'warning');
        return;
    }
    
    let logContent = '# Estate Planning Concierge v4.0 - System Log Export\n';
    logContent += `# Generated: ${new Date().toLocaleString()}\n`;
    logContent += `# Total Entries: ${logEntries.length}\n\n`;
    
    logEntries.forEach(entry => {
        const timestamp = entry.querySelector('.log-timestamp')?.textContent || '';
        const message = entry.querySelector('.log-message')?.textContent || '';
        const level = entry.className.includes('log-error') ? 'ERROR' :
                     entry.className.includes('log-warning') ? 'WARNING' :
                     entry.className.includes('log-success') ? 'SUCCESS' :
                     entry.className.includes('log-debug') ? 'DEBUG' : 'INFO';
        
        logContent += `${timestamp} [${level}] ${message}\n`;
    });
    
    // Create and download file
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `system-log-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    showToast(`Exported ${logEntries.length} log entries`, 'success');
}

// Update log count display
function updateLogCount() {
    const logHeader = document.querySelector('.log-header');
    if (logHeader) {
        const actualCount = document.querySelectorAll('#log-container .log-entry').length;
        logHeader.setAttribute('data-log-count', actualCount.toString());
    }
}

// Auto-open log section on page load (as requested)
function autoOpenLogSection() {
    const logSection = document.querySelector('.log-section');
    if (logSection) {
        // Ensure log section is visible
        logSection.style.display = 'block';
        
        // Scroll to log section smoothly
        setTimeout(() => {
            logSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'end' 
            });
        }, 500);
        
        // Add initial system message
        appendLogMessage({
            level: 'info',
            message: '🏛️ Estate Planning Concierge v4.0 Dashboard initialized - Live logging active',
            timestamp: Date.now()
        });
    }
}

// Enhanced WebSocket connection with comprehensive logging
function enhancedInitWebSocket() {
    initWebSocket(); // Call original function
    
    // Add connection status logging
    if (socket) {
        socket.on('connect', function() {
            appendLogMessage({
                level: 'success',
                message: '🔗 WebSocket connected successfully - Real-time updates enabled',
                timestamp: Date.now()
            });
        });
        
        socket.on('disconnect', function() {
            appendLogMessage({
                level: 'warning',
                message: '⚠️ WebSocket disconnected - Attempting to reconnect...',
                timestamp: Date.now()
            });
        });
        
        socket.on('reconnect', function() {
            appendLogMessage({
                level: 'success',
                message: '🔄 WebSocket reconnected successfully',
                timestamp: Date.now()
            });
        });
    }
}

// Initialize WebSocket on page load with enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Load Socket.IO library if not already loaded
    if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = '/static/js/socket.io.min.js';
        script.onload = () => {
            enhancedInitWebSocket();
            autoOpenLogSection(); // Auto-open as requested
        };
        document.head.appendChild(script);
    } else {
        enhancedInitWebSocket();
        autoOpenLogSection(); // Auto-open as requested
    }
    
    // Check for generation started flag
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('generation_started') === 'true') {
        const panel = document.getElementById('generation-status-panel');
        if (panel) {
            panel.style.display = 'block';
        }
    }
    
    // Initialize log count
    updateLogCount();
    
    // Add keyboard shortcuts for log controls
    document.addEventListener('keydown', function(e) {
        // Ctrl+Shift+C: Clear logs
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            clearLogs();
        }
        // Ctrl+Shift+E: Export logs
        else if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            exportLogs();
        }
        // Ctrl+Shift+A: Toggle auto-scroll
        else if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            toggleLogAutoScroll();
        }
    });
});

