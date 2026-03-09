"""
Django admin configuration for the chatbot application
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ChatSession, ChatMessage, IntentLog, QueryCache, ChatAnalytics, EmailAuditLog


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin interface for ChatSession model"""

    list_display = ('id', 'user_link', 'created_at', 'updated_at', 'is_active', 'message_count', 'view_messages')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def message_count(self, obj):
        """Count of messages in session"""
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def view_messages(self, obj):
        """Link to view session messages"""
        url = reverse('admin:chatbot_chatmessage_changelist') + f'?session__id={obj.id}'
        return format_html('<a href="{}">View Messages</a>', url)
    view_messages.short_description = 'Actions'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model"""

    list_display = ('id', 'session_link', 'role', 'content_preview', 'timestamp', 'has_metadata', 'sap_query')
    list_filter = ('role', 'timestamp', 'sap_query_executed')
    search_fields = ('content', 'session__user__username')
    readonly_fields = ('timestamp', 'metadata_display')
    date_hierarchy = 'timestamp'
    list_per_page = 50

    def session_link(self, obj):
        """Link to session admin page"""
        url = reverse('admin:chatbot_chatsession_change', args=[obj.session.id])
        return format_html('<a href="{}">Session {}</a>', url, obj.session.id)
    session_link.short_description = 'Session'

    def content_preview(self, obj):
        """Preview of message content"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Message'

    def has_metadata(self, obj):
        """Check if message has metadata"""
        metadata = obj.get_metadata()
        return '✓' if metadata else '✗'
    has_metadata.short_description = 'Metadata'

    def sap_query(self, obj):
        """SAP query status"""
        return '✓' if obj.sap_query_executed else '✗'
    sap_query.short_description = 'SAP Query'

    def metadata_display(self, obj):
        """Display metadata in readable format"""
        import json
        metadata = obj.get_metadata()
        if metadata:
            return format_html('<pre>{}</pre>', json.dumps(metadata, indent=2))
        return 'No metadata'
    metadata_display.short_description = 'Metadata Details'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('session', 'session__user')


@admin.register(IntentLog)
class IntentLogAdmin(admin.ModelAdmin):
    """Admin interface for IntentLog model"""

    list_display = ('id', 'message_link', 'detected_intent', 'confidence_display', 'was_successful', 'created_at')
    list_filter = ('detected_intent', 'was_successful', 'created_at')
    search_fields = ('detected_intent', 'user_feedback')
    readonly_fields = ('created_at', 'entities_display')
    date_hierarchy = 'created_at'

    def message_link(self, obj):
        """Link to message admin page"""
        url = reverse('admin:chatbot_chatmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">Message {}</a>', url, obj.message.id)
    message_link.short_description = 'Message'

    def confidence_display(self, obj):
        """Display confidence with color coding"""
        confidence = obj.confidence
        if confidence >= 0.8:
            color = 'green'
        elif confidence >= 0.6:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2%}</span>',
            color, confidence
        )
    confidence_display.short_description = 'Confidence'

    def entities_display(self, obj):
        """Display entities in readable format"""
        import json
        entities = obj.get_entities()
        if entities:
            return format_html('<pre>{}</pre>', json.dumps(entities, indent=2))
        return 'No entities'
    entities_display.short_description = 'Extracted Entities'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('message', 'message__session', 'message__session__user')


@admin.register(QueryCache)
class QueryCacheAdmin(admin.ModelAdmin):
    """Admin interface for QueryCache model"""

    list_display = ('id', 'session_link', 'query_key_short', 'created_at', 'expires_at', 'is_expired_display')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('query_key',)
    readonly_fields = ('created_at', 'results_display')
    date_hierarchy = 'created_at'

    def session_link(self, obj):
        """Link to session admin page"""
        url = reverse('admin:chatbot_chatsession_change', args=[obj.session.id])
        return format_html('<a href="{}">Session {}</a>', url, obj.session.id)
    session_link.short_description = 'Session'

    def query_key_short(self, obj):
        """Shortened query key for display"""
        return obj.query_key[:20] + '...' if len(obj.query_key) > 20 else obj.query_key
    query_key_short.short_description = 'Query Key'

    def is_expired_display(self, obj):
        """Display expiration status"""
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            time_left = obj.expires_at - timezone.now()
            minutes = int(time_left.total_seconds() / 60)
            return format_html('<span style="color: green;">✓ {} min left</span>', minutes)
    is_expired_display.short_description = 'Status'

    def results_display(self, obj):
        """Display cached results"""
        import json
        results = obj.get_results()
        if results:
            return format_html('<pre>{}</pre>', json.dumps(results, indent=2)[:1000])
        return 'No results'
    results_display.short_description = 'Cached Results'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('session', 'session__user')


@admin.register(EmailAuditLog)
class EmailAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for EmailAuditLog model - Comprehensive Email Export Audit Trail"""

    list_display = ('sent_at', 'user_link', 'recipient_email', 'product_count',
                   'status_display', 'security_flags', 'download_csv')
    list_filter = ('status', 'is_to_personal_email', 'is_admin_override', 'sent_at')
    search_fields = ('user__username', 'recipient_email', 'subject', 'ip_address')
    readonly_fields = ('sent_at', 'csv_content_display', 'user_agent_display')
    date_hierarchy = 'sent_at'
    list_per_page = 50

    fieldsets = (
        ('Email Details', {
            'fields': ('user', 'recipient_email', 'subject', 'csv_filename', 'product_count')
        }),
        ('Status & Security', {
            'fields': ('status', 'error_message', 'is_to_personal_email', 'is_admin_override')
        }),
        ('Audit Trail', {
            'fields': ('sent_at', 'ip_address', 'user_agent_display', 'session')
        }),
        ('CSV Content (Full Audit)', {
            'fields': ('csv_content_display',),
            'classes': ('collapse',),
            'description': 'Full CSV content for compliance and audit purposes'
        })
    )

    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def status_display(self, obj):
        """Display status with color coding"""
        if obj.status == 'success':
            return format_html('<span style="color: green; font-weight: bold;">✓ Success</span>')
        elif obj.status == 'failed':
            return format_html('<span style="color: red; font-weight: bold;">✗ Failed</span>')
        elif obj.status == 'blocked':
            return format_html('<span style="color: orange; font-weight: bold;">🚫 Blocked</span>')
        return obj.status
    status_display.short_description = 'Status'

    def security_flags(self, obj):
        """Display security flags"""
        flags = []
        if obj.is_to_personal_email:
            flags.append('<span style="color: orange;">⚠️ Personal Email</span>')
        if obj.is_admin_override:
            flags.append('<span style="color: blue;">👤 Admin Override</span>')
        return format_html(' '.join(flags)) if flags else '-'
    security_flags.short_description = 'Security Flags'

    def download_csv(self, obj):
        """Download link for CSV file"""
        if obj.csv_file:
            # Link to download the actual file
            return format_html(
                '<a href="{}" class="button" download>⬇️ Download CSV ({} products)</a>',
                obj.csv_file.url,
                obj.product_count
            )
        elif obj.csv_content:
            # Fallback: Show inline preview for old records
            line_count = len(obj.csv_content.split('\n')) - 1
            return format_html(
                '<span style="color: orange;">📄 View in CSV Content below ({} rows)</span>',
                line_count
            )
        return '-'
    download_csv.short_description = 'Download'

    def csv_content_display(self, obj):
        """Display CSV content in readable format"""
        if obj.csv_content:
            # Show first 50 lines of CSV
            all_lines = obj.csv_content.split('\n')
            lines = all_lines[:50]
            preview = '\n'.join(lines)
            if len(all_lines) > 50:
                remaining_rows = len(all_lines) - 50
                preview += f'\n\n... ({remaining_rows} more rows)'
            return format_html('<pre style="max-height: 400px; overflow-y: auto;">{}</pre>', preview)
        return 'No CSV content'
    csv_content_display.short_description = 'CSV Content (Preview)'

    def user_agent_display(self, obj):
        """Display user agent in readable format"""
        if obj.user_agent:
            return format_html('<small>{}</small>', obj.user_agent)
        return 'N/A'
    user_agent_display.short_description = 'User Agent'

    def has_add_permission(self, request):
        """Prevent manual addition - logs are created automatically"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion for audit trail integrity"""
        return request.user.is_superuser  # Only superusers can delete audit logs

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'session')


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for ChatAnalytics model"""

    list_display = ('date', 'total_sessions', 'total_messages', 'unique_users',
                   'success_rate', 'avg_response_time', 'avg_confidence')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Usage Metrics', {
            'fields': ('total_sessions', 'total_messages', 'unique_users')
        }),
        ('Performance Metrics', {
            'fields': ('successful_queries', 'failed_queries', 'avg_response_time_ms', 'avg_confidence_score')
        }),
        ('Intent Breakdown', {
            'fields': ('stock_queries', 'delivery_queries', 'product_info_queries',
                      'export_requests', 'help_requests')
        }),
        ('Errors', {
            'fields': ('timeout_errors', 'sap_errors')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def success_rate(self, obj):
        """Calculate and display success rate"""
        total = obj.successful_queries + obj.failed_queries
        if total > 0:
            rate = (obj.successful_queries / total) * 100
            color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, rate
            )
        return 'N/A'
    success_rate.short_description = 'Success Rate'

    def avg_response_time(self, obj):
        """Display average response time"""
        time_ms = obj.avg_response_time_ms
        if time_ms < 1000:
            return f'{time_ms:.0f} ms'
        else:
            return f'{time_ms/1000:.1f} s'
    avg_response_time.short_description = 'Avg Response'

    def avg_confidence(self, obj):
        """Display average confidence with color"""
        confidence = obj.avg_confidence_score
        if confidence >= 0.8:
            color = 'green'
        elif confidence >= 0.6:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1%}</span>',
            color, confidence
        )
    avg_confidence.short_description = 'Avg Confidence'

    def has_add_permission(self, request):
        """Prevent manual addition of analytics records"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of analytics records"""
        return False


# Customize admin site header
admin.site.site_header = "ATP Chatbot Administration"
admin.site.site_title = "ATP Chatbot Admin"
admin.site.index_title = "Chatbot Management"