/**
 * Notification System for Export Notifications
 * Polls server every 5 seconds for new notifications
 * Shows bell icon with badge and dropdown panel
 */

// Notification state
const NotificationSystem = {
    pollInterval: null,
    isOpen: false,
    unreadCount: 0,

    /**
     * Initialize notification system
     */
    init() {
        console.log('[Notifications] Initializing...');

        // Set up bell click handler
        const bell = document.getElementById('notificationBell');
        if (bell) {
            bell.addEventListener('click', (e) => {
                e.preventDefault();
                this.togglePanel();
            });
        }

        // Set up "mark all read" button
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('notificationPanel');
            const bell = document.getElementById('notificationBell');
            if (this.isOpen && panel && bell &&
                !panel.contains(e.target) &&
                !bell.contains(e.target)) {
                this.closePanel();
            }
        });

        // Start polling
        this.startPolling();

        // Fetch immediately on init
        this.fetchNotifications();
    },

    /**
     * Start polling for notifications every 5 seconds
     */
    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(() => {
            this.fetchNotifications();
        }, 5000); // Poll every 5 seconds

        console.log('[Notifications] Polling started (5s interval)');
    },

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('[Notifications] Polling stopped');
        }
    },

    /**
     * Fetch notifications from server
     */
    async fetchNotifications() {
        try {
            const response = await fetch('/atp/chat/notifications/');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.updateUI(data.notifications, data.unread_count);
            }

        } catch (error) {
            console.error('[Notifications] Error fetching:', error);
        }
    },

    /**
     * Update UI with notification data
     */
    updateUI(notifications, unreadCount) {
        this.unreadCount = unreadCount;

        // Update badge
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }

        // Update "mark all read" button visibility
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.style.display = unreadCount > 0 ? 'inline-block' : 'none';
        }

        // Update notification list
        this.renderNotifications(notifications);
    },

    /**
     * Render notifications in the panel
     */
    renderNotifications(notifications) {
        const listContainer = document.getElementById('notificationList');
        if (!listContainer) return;

        if (notifications.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="bi bi-bell-slash fs-3"></i>
                    <p class="mb-0 mt-2">No new notifications</p>
                </div>
            `;
            return;
        }

        let html = '';
        notifications.forEach(notif => {
            const time = this.formatTime(notif.created_at);
            html += `
                <div class="notification-item unread" data-id="${notif.id}">
                    <div class="notification-message">
                        <i class="bi bi-file-earmark-arrow-down text-success"></i>
                        ${notif.message}
                    </div>
                    <div class="notification-time">
                        <i class="bi bi-clock"></i> ${time}
                    </div>
                    ${notif.export_id ? `
                        <button class="notification-download-btn" onclick="NotificationSystem.downloadFile(${notif.export_id}, ${notif.id})">
                            <i class="bi bi-download"></i> Download (${notif.product_count} products)
                        </button>
                    ` : ''}
                </div>
            `;
        });

        listContainer.innerHTML = html;
    },

    /**
     * Format timestamp to relative time
     */
    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

        return date.toLocaleDateString();
    },

    /**
     * Toggle notification panel open/closed
     */
    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    },

    /**
     * Open notification panel
     */
    openPanel() {
        const panel = document.getElementById('notificationPanel');
        if (panel) {
            panel.style.display = 'block';
            this.isOpen = true;
            console.log('[Notifications] Panel opened');
        }
    },

    /**
     * Close notification panel
     */
    closePanel() {
        const panel = document.getElementById('notificationPanel');
        if (panel) {
            panel.style.display = 'none';
            this.isOpen = false;
            console.log('[Notifications] Panel closed');
        }
    },

    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
        try {
            const csrftoken = this.getCookie('csrftoken');

            const response = await fetch('/atp/chat/notifications/mark-read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ notification_id: 'all' })
            });

            const data = await response.json();

            if (data.success) {
                console.log('[Notifications] All marked as read');
                this.fetchNotifications(); // Refresh
            }

        } catch (error) {
            console.error('[Notifications] Error marking as read:', error);
        }
    },

    /**
     * Download file and mark notification as read
     */
    async downloadFile(exportId, notificationId) {
        try {
            // Open secure download endpoint
            window.open(`/atp/chat/download/${exportId}/`, '_blank');

            // Mark notification as read
            const csrftoken = this.getCookie('csrftoken');

            await fetch('/atp/chat/notifications/mark-read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ notification_id: notificationId })
            });

            // Refresh notifications
            setTimeout(() => {
                this.fetchNotifications();
            }, 500);

        } catch (error) {
            console.error('[Notifications] Error downloading file:', error);
        }
    },

    /**
     * Get CSRF token from cookie
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        NotificationSystem.init();
    });
} else {
    NotificationSystem.init();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    NotificationSystem.stopPolling();
});
