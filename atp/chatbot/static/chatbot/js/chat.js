// ATP AI Search - Modern Interface
(function() {
    'use strict';

    // ==================== DOM Elements with Null Checks ====================
    const elements = {
        searchForm: document.getElementById('search-form'),
        searchInput: document.getElementById('search-input'),
        searchButton: document.getElementById('search-button'),
        autocompleteDropdown: document.getElementById('autocomplete-dropdown'),

        conversationThread: document.getElementById('conversation-thread'),
        messagesContainer: document.getElementById('messages-container'),
        emptyState: document.getElementById('empty-conversation-state'),

        exportContainer: document.getElementById('export-container'),
        exportExcel: document.getElementById('export-excel'),
        exportEmail: document.getElementById('export-email'),

        historyList: document.getElementById('history-list'),
        clearHistoryBtn: document.getElementById('clear-history-btn'),
        newSearchBtn: document.getElementById('new-search-btn'),

        sessionIdInput: document.getElementById('session-id'),
        csrfTokenInput: document.getElementById('csrf-token')
    };

    // Validate required elements
    if (!elements.searchForm || !elements.searchInput) {
        console.error('Critical elements missing. Chat interface cannot initialize.');
        return;
    }

    // Plant modal (jQuery)
    const plantModal = typeof $ !== 'undefined' ? $('#plantSelectionModal') : null;

    // ==================== State ====================
    let state = {
        sessionId: elements.sessionIdInput ? elements.sessionIdInput.value : '',
        currentResults: null,
        currentMessageId: null,
        isProcessing: false,
        autocompleteTimeout: null,
        selectedSuggestionIndex: -1,
        currentSuggestions: []
    };

    // CSRF Token
    const csrftoken = elements.csrfTokenInput ? elements.csrfTokenInput.value : '';
    if (!csrftoken) {
        console.warn('CSRF token not found - some features may not work');
    }

    // ==================== Autocomplete Functions ====================

    async function fetchAutocompleteSuggestions(query) {
        if (!query || query.length < 2) {
            hideAutocomplete();
            return;
        }

        try {
            const response = await fetch(`/atp/chat/autocomplete/?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success && data.suggestions && data.suggestions.length > 0) {
                displayAutocompleteSuggestions(data.suggestions);
            } else {
                hideAutocomplete();
            }
        } catch (error) {
            console.error('Autocomplete error:', error);
            hideAutocomplete();
        }
    }

    function displayAutocompleteSuggestions(suggestions) {
        if (!elements.autocompleteDropdown) return;

        state.currentSuggestions = suggestions;
        state.selectedSuggestionIndex = -1;
        elements.autocompleteDropdown.innerHTML = '';

        suggestions.forEach((suggestion, index) => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            div.dataset.index = index;

            const iconSpan = document.createElement('span');
            iconSpan.className = 'autocomplete-icon';
            iconSpan.textContent = suggestion.icon || '🔍';

            const textDiv = document.createElement('div');
            textDiv.className = 'autocomplete-text';

            const mainText = document.createElement('div');
            mainText.className = 'autocomplete-main';
            mainText.textContent = suggestion.text;
            textDiv.appendChild(mainText);

            if (suggestion.description) {
                const descText = document.createElement('div');
                descText.className = 'autocomplete-desc';
                descText.textContent = suggestion.description;
                textDiv.appendChild(descText);
            }

            div.appendChild(iconSpan);
            div.appendChild(textDiv);

            div.addEventListener('click', () => selectSuggestion(suggestion.text));
            div.addEventListener('mouseenter', () => {
                state.selectedSuggestionIndex = index;
                updateSuggestionHighlight();
            });

            elements.autocompleteDropdown.appendChild(div);
        });

        elements.autocompleteDropdown.style.display = 'block';
    }

    function hideAutocomplete() {
        if (elements.autocompleteDropdown) {
            elements.autocompleteDropdown.style.display = 'none';
        }
        state.currentSuggestions = [];
        state.selectedSuggestionIndex = -1;
    }

    function selectSuggestion(text) {
        const cleanText = text.replace(/\[product number\]/gi, '')
                             .replace(/\[number1\]/gi, '')
                             .replace(/\[number2\]/gi, '')
                             .trim();

        elements.searchInput.value = cleanText;
        hideAutocomplete();
        elements.searchInput.focus();
    }

    function updateSuggestionHighlight() {
        if (!elements.autocompleteDropdown) return;

        const suggestions = elements.autocompleteDropdown.querySelectorAll('.autocomplete-item');
        suggestions.forEach((div, index) => {
            div.classList.toggle('active', index === state.selectedSuggestionIndex);
        });
    }

    function navigateSuggestions(direction) {
        if (state.currentSuggestions.length === 0) return;

        if (direction === 'down') {
            state.selectedSuggestionIndex = Math.min(
                state.selectedSuggestionIndex + 1,
                state.currentSuggestions.length - 1
            );
        } else if (direction === 'up') {
            state.selectedSuggestionIndex = Math.max(state.selectedSuggestionIndex - 1, -1);
        }

        updateSuggestionHighlight();

        if (state.selectedSuggestionIndex >= 0 && elements.autocompleteDropdown) {
            const suggestions = elements.autocompleteDropdown.querySelectorAll('.autocomplete-item');
            if (suggestions[state.selectedSuggestionIndex]) {
                suggestions[state.selectedSuggestionIndex].scrollIntoView({
                    block: 'nearest',
                    behavior: 'smooth'
                });
            }
        }
    }

    // ==================== Search Functions ====================

    // ==================== Conversation Thread Functions ====================

    function addMessageToThread(role, content, results = null, timestamp = null, exportReady = false, exportFormat = null) {
        if (!elements.messagesContainer || !elements.conversationThread) return;

        // Show thread and hide empty state
        if (elements.conversationThread.style.display === 'none') {
            elements.conversationThread.style.display = 'block';
        }
        if (elements.emptyState) {
            elements.emptyState.style.display = 'none';
        }

        // Create message wrapper
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper message-${role}`;

        // Create message content container
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Format timestamp
        const time = timestamp ? new Date(timestamp) : new Date();
        const timeString = time.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });

        if (role === 'user') {
            // User message (simple text)
            messageContent.innerHTML = `
                <div>${escapeHtml(content)}</div>
                <div class="message-timestamp">${timeString}</div>
            `;
        } else if (role === 'assistant') {
            // Assistant message (may include results table)
            let html = `<div>${formatSummaryText(content)}</div>`;

            // Only show table for multiple products OR if user explicitly wants detailed comparison
            // Don't show table for: single product, export requests, greetings, help
            const shouldShowTable = results && results.length > 1 && !exportReady;

            if (shouldShowTable) {
                html += buildResultsPreview(results);
            }

            // Add inline export buttons if export is ready
            console.log('[DEBUG] exportReady:', exportReady, 'results:', results ? results.length : 'null', 'format:', exportFormat);

            if (exportReady) {
                if (!results || results.length === 0) {
                    console.warn('[EXPORT] No results available for export buttons');
                } else {
                    console.log('[EXPORT] Adding inline export buttons for format:', exportFormat);

                    // Determine which buttons to show based on requested format
                    const showDownload = !exportFormat || exportFormat === 'csv' || exportFormat === 'excel';
                    const showEmail = !exportFormat || exportFormat === 'email';

                    html += '<div class="inline-export-buttons" style="margin-top: 15px; display: flex; gap: 10px;">';

                    if (showDownload) {
                        html += `
                            <button class="btn btn-success btn-sm inline-download-btn" title="Download as CSV">
                                <i class="fas fa-download mr-1"></i>Download CSV
                            </button>
                        `;
                    }

                    if (showEmail) {
                        html += `
                            <button class="btn btn-primary btn-sm inline-email-btn" title="Send via Email">
                                <i class="fas fa-envelope mr-1"></i>Email Report
                            </button>
                        `;
                    }

                    html += '</div>';
                }
            }

            html += `<div class="message-timestamp">${timeString}</div>`;
            messageContent.innerHTML = html;

            // Attach event listeners to inline export buttons (only if they exist)
            if (exportReady && (results && results.length > 0)) {
                const downloadBtn = messageContent.querySelector('.inline-download-btn');
                const emailBtn = messageContent.querySelector('.inline-email-btn');

                if (downloadBtn) {
                    downloadBtn.addEventListener('click', () => {
                        console.log('[EXPORT] Download button clicked');
                        downloadCSV(getAllFieldSelections());
                    });
                }

                if (emailBtn) {
                    emailBtn.addEventListener('click', () => {
                        console.log('[EXPORT] Email button clicked');
                        handleExportEmail();
                    });

                    // AUTO-TRIGGER: If export format is email, automatically show modal
                    if (exportFormat === 'email') {
                        console.log('[AUTO-EXPORT] Automatically showing email modal for export_request with email format');
                        // Use setTimeout to ensure DOM is ready and message is rendered
                        setTimeout(() => {
                            handleExportEmail();
                        }, 500);
                    }
                }
            }
        }

        messageWrapper.appendChild(messageContent);
        elements.messagesContainer.appendChild(messageWrapper);

        // Scroll to bottom smoothly
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    function buildResultsPreview(results) {
        if (!results || results.length === 0) return '';

        let html = `
            <div class="results-preview">
                <h6><i class="fas fa-table mr-2"></i>Results (${results.length})</h6>
                <table class="results-preview-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Description</th>
                            <th>Stock</th>
                            <th>Unit</th>
                            <th>Next Delivery</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        results.forEach(item => {
            const stock = item.STOCK || item.stock || item.LABST || '0';
            const stockClass = parseInt(stock) > 0 ? 'in-stock' : 'out-of-stock';

            html += `
                <tr>
                    <td><strong>${escapeHtml(item.MATNR || item.product || '')}</strong></td>
                    <td>${escapeHtml(item.MAKTX || item.description || '')}</td>
                    <td><span class="stock-badge ${stockClass}">${stock}</span></td>
                    <td>${escapeHtml(item.MEINS || item.unit || '')}</td>
                    <td>${escapeHtml(item.EEIND || item.next_delivery || item.EINDT || 'N/A')}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    function clearConversationThread() {
        if (!elements.messagesContainer) return;
        elements.messagesContainer.innerHTML = '';
        if (elements.conversationThread) {
            elements.conversationThread.style.display = 'none';
        }
        if (elements.emptyState) {
            elements.emptyState.style.display = 'block';
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatSummaryText(text) {
        if (!text) return '';

        // Replace markdown-style images ![alt](url) with actual <img> tags
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function(match, alt, url) {
            return `<img src="${url}" alt="${alt}" class="product-image" style="max-width: 300px; max-height: 300px; display: block; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">`;
        });

        // Replace markdown-style links [text](url) with actual <a> tags
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, linkText, url) {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #0056b3; text-decoration: underline; font-weight: 600;">${linkText}</a>`;
        });

        // Replace markdown-style bold **text** with <strong>text</strong>
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Replace line breaks with <br>
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    // ==================== Search Functions ====================

    async function handleSearch(e) {
        if (e) e.preventDefault();

        // If suggestion is selected, use it
        if (state.selectedSuggestionIndex >= 0 && state.currentSuggestions[state.selectedSuggestionIndex]) {
            selectSuggestion(state.currentSuggestions[state.selectedSuggestionIndex].text);
            return;
        }

        const query = elements.searchInput.value.trim();
        if (!query || state.isProcessing) return;

        hideAutocomplete();

        // Create a new session if we don't have one (after clearing history)
        if (!state.sessionId) {
            console.log('[SEARCH] No session ID, creating new session');
            await createNewSession();
        }

        // Add user message to thread immediately
        addMessageToThread('user', query);

        // Update UI state
        state.isProcessing = true;
        elements.searchInput.disabled = true;
        elements.searchButton.disabled = true;
        elements.searchButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span>Sending...';

        // Clear input immediately for better UX
        elements.searchInput.value = '';

        try {
            // Create AbortController for timeout (5 minutes for large queries)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

            const response = await fetch('/atp/chat/message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    message: query
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const data = await response.json();

            if (data.success) {
                state.currentMessageId = data.message_id;

                // Add assistant message to thread with results (and inline export buttons if export is ready)
                addMessageToThread('assistant', data.response, data.results, null, data.export_ready, data.export_format);

                if (data.requires_plant_selection && data.available_plants) {
                    showPlantSelection(data.available_plants);
                }

                // Handle large query email trigger
                if (data.trigger_large_query_email) {
                    // Auto-trigger the large query email export (download + email)
                    triggerLargeQueryEmail(data.email_address);
                }

                if (data.trigger_large_query_download) {
                    // Auto-trigger the large query download (download only, no email)
                    triggerLargeQueryDownload();
                }

                // Handle large query choice (show buttons)
                if (data.needs_user_choice && data.choice_type === 'large_query') {
                    showLargeQueryChoiceButtons(data.total_products);
                }

                if (data.results && data.results.length > 0) {
                    state.currentResults = data.results;
                    console.log('Results received:', data.results); // DEBUG
                }

                // ALWAYS hide bottom export container - we only use inline buttons now
                if (elements.exportContainer) {
                    elements.exportContainer.style.display = 'none';
                }

                loadHistory();

                if (window.DEBUG) {
                    console.log('Intent:', data.intent, 'Confidence:', data.confidence);
                }
            } else {
                addMessageToThread('assistant', data.error || 'An error occurred. Please try again.');
            }

        } catch (error) {
            console.error('Search error:', error);

            // Distinguish between timeout and other errors
            if (error.name === 'AbortError') {
                displayError('⏱️ Query timeout. Large queries (400+ products) can take several minutes. Please try again - your query may still be processing.');
            } else {
                displayError('⚠️ Connection error. Please check your network and try again.');
            }
        } finally {
            state.isProcessing = false;
            elements.searchInput.disabled = false;
            elements.searchButton.disabled = false;
            elements.searchButton.innerHTML = '<span class="btn-text">Send</span><i class="fas fa-paper-plane ml-2"></i>';
            elements.searchInput.focus();
        }
    }

    function displayError(message) {
        // Display error as assistant message in thread
        addMessageToThread('assistant', `⚠️ ${message}`);
    }

    // ==================== Export Functions ====================

    // ==================== History Functions ====================

    async function loadHistory() {
        if (!elements.historyList || !state.sessionId) return;

        try {
            const response = await fetch(`/atp/chat/history/${state.sessionId}/`);
            const data = await response.json();

            if (data.success && data.history && data.history.length > 0) {
                displayHistory(data.history);
            } else {
                displayEmptyHistory();
            }

            // Also load all sessions for sidebar
            loadAllSessions();
        } catch (error) {
            console.error('Error loading history:', error);
            displayEmptyHistory();
        }
    }

    async function loadAllSessions() {
        if (!elements.historyList) return;

        try {
            const response = await fetch('/atp/chat/sessions/');
            const data = await response.json();

            if (data.success && data.sessions && data.sessions.length > 0) {
                displayAllSessions(data.sessions);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    function displayHistory(history) {
        if (!elements.historyList) return;

        // Clear and populate conversation thread with ALL messages
        if (elements.messagesContainer) {
            elements.messagesContainer.innerHTML = '';

            if (history.length > 0) {
                history.forEach(msg => {
                    // Get metadata to check if message has results
                    const metadata = msg.metadata || {};
                    const results = metadata.results || null;  // Results are now saved directly in metadata
                    const exportReady = metadata.intent === 'export_request' && results !== null;
                    const exportFormat = metadata.entities?.export_format || null;

                    addMessageToThread(msg.role, msg.content, results, msg.timestamp, exportReady, exportFormat);
                });

                // Show conversation thread and hide empty state
                if (elements.conversationThread) {
                    elements.conversationThread.style.display = 'block';
                }
                if (elements.emptyState) {
                    elements.emptyState.style.display = 'none';
                }
            } else {
                // No history - show empty state
                if (elements.emptyState) {
                    elements.emptyState.style.display = 'block';
                }
            }
        }

        // Hide export-container if last message was an export request
        const lastAssistantMsg = [...history].reverse().find(msg => msg.role === 'assistant');
        if (lastAssistantMsg && lastAssistantMsg.metadata) {
            const isExportIntent = lastAssistantMsg.metadata.intent === 'export_request';
            if (isExportIntent && elements.exportContainer) {
                elements.exportContainer.style.display = 'none';
            }
        }
    }

    function displayAllSessions(sessions) {
        console.log('[SESSIONS] Displaying all sessions:', sessions.length);
        if (!elements.historyList) return;

        elements.historyList.innerHTML = '';

        if (sessions.length === 0) {
            displayEmptyHistory();
            return;
        }

        console.log('[SESSIONS] Rendering', sessions.length, 'conversation threads');
        sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.style.position = 'relative';

            // Mark current session as active
            if (session.id === state.sessionId) {
                item.classList.add('active');
            }

            const timeDiv = document.createElement('div');
            timeDiv.className = 'history-time';
            timeDiv.textContent = formatHistoryTime(session.updated_at);

            const textDiv = document.createElement('div');
            textDiv.className = 'history-text';
            textDiv.textContent = truncateText(session.preview, 50);

            // Add message count badge
            const badge = document.createElement('span');
            badge.className = 'message-count-badge';
            badge.textContent = session.message_count;
            badge.style.cssText = 'margin-left: 8px; background: #e3e3e8; padding: 2px 8px; border-radius: 10px; font-size: 11px; color: #666;';

            textDiv.appendChild(badge);

            // Add delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-session-btn';
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            deleteBtn.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: transparent; border: none; color: #999; cursor: pointer; opacity: 0; transition: opacity 0.2s; padding: 5px; font-size: 14px;';
            deleteBtn.title = 'Delete conversation';

            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation(); // Don't trigger session switch
                await deleteSession(session.id);
            });

            // Show delete button on hover
            item.addEventListener('mouseenter', () => {
                deleteBtn.style.opacity = '1';
            });
            item.addEventListener('mouseleave', () => {
                deleteBtn.style.opacity = '0';
            });

            item.appendChild(timeDiv);
            item.appendChild(textDiv);
            item.appendChild(deleteBtn);

            item.addEventListener('click', async () => {
                // Switch to this session
                if (session.id !== state.sessionId) {
                    state.sessionId = session.id;
                    await loadHistory();
                }
            });

            elements.historyList.appendChild(item);
        });
    }

    function displayEmptyHistory() {
        if (!elements.historyList) return;

        elements.historyList.innerHTML = `
            <div class="empty-state text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3 opacity-50"></i>
                <p class="text-muted mb-0 small">Your searches will appear here</p>
            </div>
        `;
    }

    function formatHistoryTime(timestamp) {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            const hours = diff / (1000 * 60 * 60);

            if (hours < 1) {
                const minutes = Math.floor(diff / (1000 * 60));
                return `${minutes}m ago`;
            } else if (hours < 24) {
                return `${Math.floor(hours)}h ago`;
            } else {
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }
        } catch (e) {
            return '';
        }
    }

    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    async function deleteSession(sessionId) {
        showConfirmModal('Delete this conversation?', async () => {
            console.log('[DELETE] Attempting to delete session:', sessionId);

            try {
                const response = await fetch(`/atp/chat/session/${sessionId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    }
                });

                console.log('[DELETE] Response status:', response.status);
                const data = await response.json();
                console.log('[DELETE] Response data:', data);

                if (data.success) {
                    console.log('[DELETE] Successfully deleted session', sessionId);

                    // If deleted current session, create new one first
                    if (sessionId === state.sessionId) {
                        console.log('[DELETE] Deleted current session, creating new one');
                        await createNewSession();
                    } else {
                        // Just reload session list if not current
                        await loadAllSessions();
                    }

                    showToast('Conversation deleted');
                } else {
                    console.error('[DELETE] Delete failed:', data.error);
                    showToast('Error deleting conversation: ' + (data.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('[DELETE] Exception during delete:', error);
                showToast('Error deleting conversation', 'error');
            }
        });
    }

    async function clearHistory() {
        console.log('[CLEAR_HISTORY] Button clicked');

        showConfirmModal('Clear all search history? This cannot be undone.', async () => {
            console.log('[CLEAR_HISTORY] User confirmed');
            console.log('[CLEAR_HISTORY] Attempting to delete all sessions');

        try {
            const response = await fetch('/atp/chat/sessions/delete-all/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            });

            console.log('[CLEAR_HISTORY] Response status:', response.status);
            const data = await response.json();
            console.log('[CLEAR_HISTORY] Response data:', data);

            if (data.success) {
                console.log('[CLEAR_HISTORY] Deleted', data.count, 'sessions');

                // Check if there was nothing to delete
                if (data.nothing_to_delete) {
                    showToast('Nothing to delete', 'info');
                    return;
                }

                // Clear the UI without creating a new session
                clearConversationThread();
                displayEmptyHistory();
                state.sessionId = '';
                state.currentResults = null;
                state.currentMessageId = null;

                if (elements.sessionIdInput) {
                    elements.sessionIdInput.value = '';
                }

                showToast(`${data.count} conversation(s) deleted`);
            } else {
                console.error('[CLEAR_HISTORY] Delete failed:', data.error);
                showToast('Error deleting conversations: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('[CLEAR_HISTORY] Exception:', error);
            showToast('Error deleting conversations', 'error');
        }
        });
    }

    // ==================== Confirmation Modal ====================

    function showConfirmModal(message, onConfirm) {
        const confirmModal = typeof $ !== 'undefined' ? $('#confirmModal') : null;
        if (!confirmModal) {
            // Fallback to native confirm if jQuery/modal not available
            if (confirm(message)) {
                onConfirm();
            }
            return;
        }

        // Set message
        document.getElementById('confirmModalMessage').textContent = message;

        // Remove old event listeners and add new one
        const confirmBtn = document.getElementById('confirmModalBtn');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.addEventListener('click', () => {
            confirmModal.modal('hide');
            onConfirm();
        });

        // Show modal
        confirmModal.modal('show');
    }

    // ==================== Feedback Functions ====================

    async function submitFeedback(rating) {
        if (!state.currentMessageId) {
            console.error('No message ID for feedback');
            return;
        }

        try {
            const response = await fetch('/atp/chat/feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    message_id: state.currentMessageId,
                    rating: rating
                })
            });

            const data = await response.json();

            if (data.success) {
                showToast('Thank you for your feedback!');
            }
        } catch (error) {
            console.error('Feedback error:', error);
        }
    }

    function showToast(message, type = 'success') {
        // Determine icon and color based on type
        const iconMap = {
            success: '<i class="fas fa-check-circle mr-2"></i>',
            error: '<i class="fas fa-exclamation-circle mr-2"></i>',
            info: '<i class="fas fa-info-circle mr-2"></i>',
            warning: '<i class="fas fa-exclamation-triangle mr-2"></i>'
        };

        const colorMap = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8',
            warning: '#ffc107'
        };

        const icon = iconMap[type] || iconMap.success;
        const color = colorMap[type] || colorMap.success;

        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'custom-toast';
        toast.style.background = color;
        toast.innerHTML = icon + message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ==================== Export Functions ====================

    const exportFieldsModal = typeof $ !== 'undefined' ? $('#exportFieldsModal') : null;
    const emailExportModal = typeof $ !== 'undefined' ? $('#emailExportModal') : null;

    async function handleExportExcel() {
        if (!state.currentResults || state.currentResults.length === 0) {
            alert('No results to export');
            return;
        }

        // Show field selection modal
        if (exportFieldsModal) {
            exportFieldsModal.modal('show');
        } else {
            // Fallback: download all fields
            downloadCSV(getAllFieldSelections());
        }
    }

    async function handleExportEmail() {
        if (!state.currentResults || state.currentResults.length === 0) {
            alert('No results to export');
            return;
        }

        // Show email input modal
        if (emailExportModal) {
            emailExportModal.modal('show');
        }
    }

    function getAllFieldSelections() {
        return {
            product: true,
            description: true,
            brand: true,
            stock: true,
            unit: true,
            delivery: true,
            quantity: true,
            upc: true,
            weight: true,
            origin: true,
            vendor: true,
            po: true,
            casepack: true
        };
    }

    function getSelectedFields() {
        return {
            product: document.getElementById('field-product')?.checked || false,
            description: document.getElementById('field-description')?.checked || false,
            brand: document.getElementById('field-brand')?.checked || false,
            stock: document.getElementById('field-stock')?.checked || false,
            unit: document.getElementById('field-unit')?.checked || false,
            delivery: document.getElementById('field-delivery')?.checked || false,
            quantity: document.getElementById('field-quantity')?.checked || false,
            upc: document.getElementById('field-upc')?.checked || false,
            weight: document.getElementById('field-weight')?.checked || false,
            origin: document.getElementById('field-origin')?.checked || false,
            vendor: document.getElementById('field-vendor')?.checked || false,
            po: document.getElementById('field-po')?.checked || false,
            casepack: document.getElementById('field-casepack')?.checked || false
        };
    }

    function downloadCSV(selectedFields) {
        if (!state.currentResults || state.currentResults.length === 0) return;

        const results = state.currentResults;
        console.log('Exporting results:', results); // DEBUG

        // Build headers based on selected fields - using ACTUAL SAP field names
        const fieldMap = {
            product: 'Product Number',
            description: 'Description',
            brand: 'Brand',
            stock: 'Current Stock',
            unit: 'Unit',
            delivery: 'Next Delivery Date',
            quantity: 'Delivery Quantity',
            upc: 'UPC/EAN',
            weight: 'Weight (kg)',
            origin: 'Country of Origin',
            vendor: 'Vendor',
            po: 'Purchase Order',
            casepack: 'Case Pack Size'
        };

        const headers = [];
        const fieldKeys = [];

        for (const [key, label] of Object.entries(fieldMap)) {
            if (selectedFields[key]) {
                headers.push(label);
                fieldKeys.push(key);
            }
        }

        if (headers.length === 0) {
            alert('Please select at least one field to export');
            return;
        }

        const csvRows = [headers.join(',')];

        // Add data rows
        results.forEach(item => {
            console.log('Item data:', item); // DEBUG
            const row = [];
            fieldKeys.forEach(key => {
                let value = '';
                switch (key) {
                    case 'product':
                        value = item.MATNR || item.product || '';
                        break;
                    case 'description':
                        value = (item.MAKTX || item.description || '').replace(/"/g, '""');
                        value = `"${value}"`;
                        break;
                    case 'brand':
                        value = (item.ZZBRAND || item.brand || '').replace(/"/g, '""');
                        value = `"${value}"`;
                        break;
                    case 'stock':
                        value = item.STOCK || item.stock || item.LABST || '0';
                        break;
                    case 'unit':
                        value = item.MEINS || item.unit || '';
                        break;
                    case 'delivery':
                        value = item.EEIND || item.next_delivery || item.EINDT || '';
                        break;
                    case 'quantity':
                        value = item.OMENG || item.delivery_qty || item.MENGE || '0';
                        break;
                    case 'upc':
                        value = item.EAN11 || item.upc || '';
                        break;
                    case 'weight':
                        value = item.BRGEW || item.weight || '';
                        break;
                    case 'origin':
                        value = item.HERKL || item.origin || '';
                        break;
                    case 'vendor':
                        value = (item.ZBRDES || item.vendor || '').replace(/"/g, '""');
                        value = `"${value}"`;
                        break;
                    case 'po':
                        value = item.EBELN || item.po || '';
                        break;
                    case 'casepack':
                        value = item.UMREZ || item.case_pack || '';
                        break;
                }
                row.push(value);
            });
            csvRows.push(row.join(','));
        });

        const csvContent = csvRows.join('\n');
        console.log('CSV Content:', csvContent); // DEBUG

        // Create blob and download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        const timestamp = new Date().toISOString().slice(0, 10);
        link.setAttribute('href', url);
        link.setAttribute('download', `product_stock_${timestamp}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast('Excel file downloaded successfully!');

        // Close modal if open
        if (exportFieldsModal) {
            exportFieldsModal.modal('hide');
        }
    }

    async function sendEmail() {
        const emailInput = document.getElementById('email-address');
        const emailAddress = emailInput ? emailInput.value.trim() : '';

        if (!emailAddress) {
            alert('Please enter an email address');
            return;
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailAddress)) {
            alert('Please enter a valid email address');
            return;
        }

        if (!state.currentResults || state.currentResults.length === 0) {
            alert('No results to export');
            return;
        }

        try {
            const response = await fetch('/atp/chat/export/email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    email_address: emailAddress,
                    results: state.currentResults
                })
            });

            const data = await response.json();

            if (data.success) {
                showToast(`Email sent to ${emailAddress}!`, 'success');
                if (emailExportModal) {
                    emailExportModal.modal('hide');
                }
            } else {
                showToast(data.error || 'Error sending email', 'error');
            }
        } catch (error) {
            console.error('Email error:', error);
            showToast('Error sending email. Please try again.', 'error');
        }
    }

    // ==================== Plant Selection ====================

    function showPlantSelection(plants) {
        if (!plantModal) return;

        const plantList = document.getElementById('plant-selection-list');
        if (!plantList) return;

        plantList.innerHTML = '';

        plants.forEach(plant => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
                <strong>${plant.code}</strong>
                <br>
                <small class="text-muted">${plant.description}</small>
            `;

            item.onclick = (e) => {
                e.preventDefault();
                selectPlant(plant.code);
                plantModal.modal('hide');
            };

            plantList.appendChild(item);
        });

        plantModal.modal('show');
    }

    function selectPlant(plantCode) {
        elements.searchInput.value = `Use plant ${plantCode}`;
        handleSearch();
    }

    // ==================== Session Management ====================

    async function createNewSession() {
        try {
            const response = await fetch('/atp/chat/session/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            });

            const data = await response.json();

            if (data.success) {
                state.sessionId = data.session_id;
                if (elements.sessionIdInput) {
                    elements.sessionIdInput.value = state.sessionId;
                }

                // Clear conversation thread
                clearConversationThread();
                if (elements.exportContainer) elements.exportContainer.style.display = 'none';
                state.currentResults = null;
                state.currentMessageId = null;
                elements.searchInput.value = '';

                loadHistory();
                showToast('New search session started');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            alert('Error starting new session. Please refresh the page.');
        }
    }

    // ==================== Event Listeners ====================

    if (elements.searchForm) {
        elements.searchForm.addEventListener('submit', handleSearch);
    }

    if (elements.searchInput) {
        elements.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            if (state.autocompleteTimeout) {
                clearTimeout(state.autocompleteTimeout);
            }

            state.autocompleteTimeout = setTimeout(() => {
                fetchAutocompleteSuggestions(query);
            }, 300);
        });

        elements.searchInput.addEventListener('keydown', (e) => {
            if (!elements.autocompleteDropdown || elements.autocompleteDropdown.style.display === 'none') return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                navigateSuggestions('down');
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                navigateSuggestions('up');
            } else if (e.key === 'Escape') {
                hideAutocomplete();
            }
        });
    }

    document.addEventListener('click', (e) => {
        if (!elements.searchInput.contains(e.target) &&
            (!elements.autocompleteDropdown || !elements.autocompleteDropdown.contains(e.target))) {
            hideAutocomplete();
        }
    });

    if (elements.exportExcel) {
        elements.exportExcel.addEventListener('click', handleExportExcel);
    }

    if (elements.exportEmail) {
        elements.exportEmail.addEventListener('click', handleExportEmail);
    }

    if (elements.clearHistoryBtn) {
        console.log('[INIT] Clear history button found, attaching listener');
        elements.clearHistoryBtn.addEventListener('click', clearHistory);
    } else {
        console.error('[INIT] Clear history button NOT FOUND!');
    }

    if (elements.newSearchBtn) {
        elements.newSearchBtn.addEventListener('click', async () => {
            if (confirm('Start a new conversation? Your previous conversations will be saved in the sidebar.')) {
                await createNewSession();
            }
        });
    }

    // ==================== Modal Event Listeners ====================

    // Export field selection modal buttons
    const confirmExportBtn = document.getElementById('confirm-export-btn');
    if (confirmExportBtn) {
        confirmExportBtn.addEventListener('click', () => {
            const selectedFields = getSelectedFields();
            downloadCSV(selectedFields);
        });
    }

    const selectAllFieldsBtn = document.getElementById('select-all-fields');
    if (selectAllFieldsBtn) {
        selectAllFieldsBtn.addEventListener('click', () => {
            document.querySelectorAll('#exportFieldsModal input[type="checkbox"]').forEach(cb => {
                cb.checked = true;
            });
        });
    }

    const deselectAllFieldsBtn = document.getElementById('deselect-all-fields');
    if (deselectAllFieldsBtn) {
        deselectAllFieldsBtn.addEventListener('click', () => {
            document.querySelectorAll('#exportFieldsModal input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
        });
    }

    // Email export modal button
    const confirmEmailBtn = document.getElementById('confirm-email-btn');
    if (confirmEmailBtn) {
        confirmEmailBtn.addEventListener('click', sendEmail);
    }

    // Email input - submit on Enter
    const emailAddressInput = document.getElementById('email-address');
    if (emailAddressInput) {
        emailAddressInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendEmail();
            }
        });
    }

    // ==================== Large Query Functions ====================

    function showLargeQueryChoiceButtons(totalProducts) {
        // Create choice buttons container
        const choiceContainer = document.createElement('div');
        choiceContainer.className = 'large-query-choice-container mb-3';
        choiceContainer.innerHTML = `
            <div class="btn-group w-100" role="group">
                <button type="button" class="btn btn-primary large-query-choice" data-choice="show">
                    <i class="fas fa-eye"></i> Show First 200
                </button>
                <button type="button" class="btn btn-info large-query-choice" data-choice="email">
                    <i class="fas fa-envelope"></i> Email All ${totalProducts}
                </button>
            </div>
        `;

        // Append to messages container
        if (elements.messagesContainer) {
            elements.messagesContainer.appendChild(choiceContainer);
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }

        // Add click handlers
        choiceContainer.querySelectorAll('.large-query-choice').forEach(btn => {
            btn.addEventListener('click', function() {
                const choice = this.dataset.choice;
                // Remove buttons after selection
                choiceContainer.remove();

                // Send user's choice as a message
                if (choice === 'show') {
                    handleSearch('Show first 200 products');
                } else if (choice === 'email') {
                    handleSearch('Email me the complete report');
                }
            });
        });
    }

    async function triggerLargeQueryEmail(emailAddress) {
        try {
            const response = await fetch('/atp/chat/export/large-query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    email_address: emailAddress
                })
            });

            const data = await response.json();

            if (data.success) {
                // Show success message in chat
                const message = data.message || data.response || 'Report sent successfully!';
                addMessageToThread('assistant', `✅ ${message}`);
            } else {
                addMessageToThread('assistant', `⚠️ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error triggering large query email:', error);
            addMessageToThread('assistant', '⚠️ Error sending email export. Please try again.');
        }
    }

    async function triggerLargeQueryDownload() {
        try {
            const response = await fetch('/atp/chat/export/download-only/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    session_id: state.sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Show success message in chat
                const message = data.response || data.message || 'Download ready!';
                addMessageToThread('assistant', message);
            } else {
                addMessageToThread('assistant', `⚠️ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error triggering large query download:', error);
            addMessageToThread('assistant', '⚠️ Error preparing download. Please try again.');
        }
    }

    // ==================== Initialization ====================

    if (elements.searchInput) {
        elements.searchInput.focus();
    }

    if (state.sessionId) {
        loadHistory();
    }

    // Debug mode
    if (window.DEBUG) {
        window.searchDebug = {
            search: handleSearch,
            createSession: createNewSession,
            downloadCSV: downloadCSV,
            state: state
        };
        console.log('Debug mode: Use window.searchDebug');
    }

})();
