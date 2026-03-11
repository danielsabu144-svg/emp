from django.contrib import admin
from .models import Notification, ChatbotResponse, ChatHistory

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    date_hierarchy = 'created_at'


@admin.register(ChatbotResponse)
class ChatbotResponseAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('keyword', 'response')


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'question', 'response')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
