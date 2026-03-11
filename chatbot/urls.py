from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('api/', views.chatbot_api, name='chatbot_api'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/send/', views.send_notification, name='send_notification'),
]
