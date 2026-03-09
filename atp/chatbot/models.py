"""
Database models for the chatbot application
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ChatSession(models.Model):
    """Track conversation sessions for each user"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Store conversation context as JSON
    # Example: {'selected_plant': '1001', 'last_query_type': 'stock_check', 'cached_results': [...]}
    context = models.TextField(default='{}')

    def get_context(self):
        """Get context as dictionary"""
        try:
            return json.loads(self.context)
        except:
            return {}

    def update_context(self, context_dict):
        """Update context from dictionary"""
        self.context = json.dumps(context_dict)
        self.save()

    def __str__(self):
        return f"Session {self.id} - {self.user.username} - {self.created_at}"

    class Meta:
        ordering = ['-updated_at']
        db_table = 'chatbot_sessions'


class ChatMessage(models.Model):
    """Individual messages in a conversation"""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Store metadata like intent, entities, confidence
    # Example: {'intent': 'stock_query', 'confidence': 0.95, 'entities': {'products': ['12345']}}
    metadata = models.TextField(default='{}')

    # Track if this message resulted in a SAP query
    sap_query_executed = models.BooleanField(default=False)

    def get_metadata(self):
        """Get metadata as dictionary"""
        try:
            return json.loads(self.metadata)
        except:
            return {}

    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.metadata = json.dumps(metadata_dict)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    class Meta:
        ordering = ['timestamp']
        db_table = 'chatbot_messages'


class IntentLog(models.Model):
    """Log intent classifications for analysis and improvement"""

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='intent_logs')
    detected_intent = models.CharField(max_length=50)
    confidence = models.FloatField()

    # Store extracted entities
    entities = models.TextField(default='{}')

    # Track if the intent was correct (for learning)
    was_successful = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_entities(self):
        """Get entities as dictionary"""
        try:
            return json.loads(self.entities)
        except:
            return {}

    def __str__(self):
        return f"{self.detected_intent} ({self.confidence:.2f})"

    class Meta:
        ordering = ['-created_at']
        db_table = 'chatbot_intent_logs'


class QueryCache(models.Model):
    """Cache SAP query results to reduce API calls"""

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='cached_queries')
    query_key = models.CharField(max_length=255, db_index=True)  # Hash of plant + products
    results = models.TextField()  # JSON serialized results
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        """Check if cache entry has expired"""
        return timezone.now() > self.expires_at

    def get_results(self):
        """Get results as dictionary"""
        try:
            return json.loads(self.results)
        except:
            return None

    class Meta:
        ordering = ['-created_at']
        db_table = 'chatbot_query_cache'
        indexes = [
            models.Index(fields=['query_key', 'expires_at']),
        ]


class MessageFeedback(models.Model):
    """User feedback on chatbot responses for model improvement"""

    RATING_CHOICES = [
        (1, 'Thumbs Up'),
        (-1, 'Thumbs Down'),
    ]

    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback',
        limit_choices_to={'role': 'assistant'}
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, help_text="Optional user comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track what was wrong (for thumbs down)
    issue_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('incorrect_intent', 'Wrong Intent Detected'),
            ('incorrect_info', 'Incorrect Information'),
            ('missing_info', 'Missing Information'),
            ('confusing', 'Response Confusing'),
            ('slow', 'Too Slow'),
            ('other', 'Other'),
        ]
    )

    def __str__(self):
        rating_text = "👍" if self.rating == 1 else "👎"
        return f"{rating_text} on message {self.message.id}"

    class Meta:
        ordering = ['-created_at']
        db_table = 'chatbot_message_feedback'
        indexes = [
            models.Index(fields=['rating', 'created_at']),
        ]


class EmailAuditLog(models.Model):
    """
    Comprehensive audit log for all email exports
    Tracks who sent what to whom for compliance and security
    """

    # Who triggered the email
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='email_exports')

    # Email details
    recipient_email = models.EmailField(help_text="Email address where report was sent")
    subject = models.CharField(max_length=255)

    # What was sent
    csv_filename = models.CharField(max_length=255)
    csv_content = models.TextField(help_text="Full CSV content for audit trail")
    csv_file = models.FileField(
        upload_to='email_exports/%Y/%m/',
        null=True,
        blank=True,
        help_text="CSV file attachment for download"
    )
    product_count = models.IntegerField(help_text="Number of products in export")

    # When
    sent_at = models.DateTimeField(auto_now_add=True)

    # Context
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_exports'
    )

    # Status tracking
    STATUS_CHOICES = [
        ('success', 'Sent Successfully'),
        ('failed', 'Failed to Send'),
        ('blocked', 'Blocked by Policy'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True, help_text="Error details if failed")

    # Security flags
    is_to_personal_email = models.BooleanField(
        default=False,
        help_text="Flag if sent to non-company email"
    )
    is_admin_override = models.BooleanField(
        default=False,
        help_text="Admin sent to different email address"
    )

    # IP tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} → {self.recipient_email} ({self.product_count} products) - {self.sent_at}"

    class Meta:
        ordering = ['-sent_at']
        db_table = 'chatbot_email_audit_log'
        indexes = [
            models.Index(fields=['user', 'sent_at']),
            models.Index(fields=['recipient_email', 'sent_at']),
            models.Index(fields=['is_to_personal_email']),
        ]
        verbose_name = "Email Audit Log"
        verbose_name_plural = "Email Audit Logs"


class ExportNotification(models.Model):
    """Notification for completed exports - shown in bell icon"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='export_notifications',
        help_text="User who receives this notification"
    )
    export_log = models.ForeignKey(
        EmailAuditLog,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The export this notification is about"
    )
    message = models.CharField(
        max_length=255,
        help_text="Notification message text"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether user has seen this notification"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.user.username} - {self.message[:50]} ({status})"

    class Meta:
        ordering = ['-created_at']
        db_table = 'chatbot_export_notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
        verbose_name = "Export Notification"
        verbose_name_plural = "Export Notifications"


class ChatAnalytics(models.Model):
    """Daily analytics for monitoring chatbot performance"""

    date = models.DateField(unique=True)

    # Usage metrics
    total_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)

    # Performance metrics
    successful_queries = models.IntegerField(default=0)
    failed_queries = models.IntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0.0)
    avg_confidence_score = models.FloatField(default=0.0)

    # Intent breakdown
    stock_queries = models.IntegerField(default=0)
    delivery_queries = models.IntegerField(default=0)
    product_info_queries = models.IntegerField(default=0)
    export_requests = models.IntegerField(default=0)
    help_requests = models.IntegerField(default=0)

    # Error tracking
    timeout_errors = models.IntegerField(default=0)
    sap_errors = models.IntegerField(default=0)

    # Feedback metrics
    thumbs_up_count = models.IntegerField(default=0)
    thumbs_down_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.date}"

    class Meta:
        ordering = ['-date']
        db_table = 'chatbot_analytics'