from django.urls import path
from . import views

urlpatterns = [
    # HR views
    path('requests/', views.leave_requests, name='leave_requests'),
    path('approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    
    # Employee views
    path('my/', views.my_leaves, name='my_leaves'),
    path('apply/', views.apply_leave, name='apply_leave'),
]
