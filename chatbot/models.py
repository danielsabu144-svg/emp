from django.db import models
from accounts.models import User

class Notification(models.Model):
    """System notifications for employees"""
    
    NOTIFICATION_TYPE_CHOICES = (
        ('BIRTHDAY', 'Birthday'),
        ('ANNIVERSARY', 'Work Anniversary'),
        ('LEAVE', 'Leave Request'),
        ('PAYROLL', 'Payroll'),
        ('GENERAL', 'General'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]


class ChatbotResponse(models.Model):
    """Predefined chatbot responses"""
    
    keyword = models.CharField(max_length=100, unique=True)
    response = models.TextField()
    category = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.keyword
    
    class Meta:
        ordering = ['category', 'keyword']


class ChatHistory(models.Model):
    """Store chat history for analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    question = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Chat Histories'
