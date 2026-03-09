"""
URL configuration for chatbot app
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Main chat interface
    path('', views.chat_view, name='chat'),

    # Debug page
    path('debug/', views.debug_view, name='debug'),

    # API endpoints
    path('session/', views.create_session, name='create_session'),
    path('sessions/', views.get_all_sessions, name='get_all_sessions'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('sessions/delete-all/', views.delete_all_sessions, name='delete_all_sessions'),
    path('message/', views.process_message, name='process_message'),
    path('history/<int:session_id>/', views.get_history, name='get_history'),
    path('autocomplete/', views.get_autocomplete, name='get_autocomplete'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('export/email/', views.export_email, name='export_email'),
    path('export/large-query/', views.export_large_query, name='export_large_query'),
    path('export/download-only/', views.download_large_query, name='download_large_query'),

    # Notification endpoints
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),

    # Download and history
    path('download/<int:export_id>/', views.download_export, name='download_export'),
    path('history/', views.export_history, name='export_history'),
]