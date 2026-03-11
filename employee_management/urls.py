"""
URL configuration for employee_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import login_view, logout_view, dashboard

urlpatterns = [
    # path('admin/', admin.site.urls), # Using custom admin instead
    
    # Authentication
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # App URLs
    path('employees/', include('employees.urls')),
    path('attendance/', include('attendance.urls')),
    path('leaves/', include('leave_management.urls')),
    path('payroll/', include('payroll.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('tasks/', include('task_management.urls')),
]

# Media files (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
