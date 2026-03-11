from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.attendance_list, name='attendance_list'),
    path('my/', views.my_attendance, name='my_attendance'),
    path('checkin/', views.mark_attendance_checkin, name='mark_attendance_checkin'),
    path('logout/', views.mark_attendance_logout, name='mark_attendance_logout'),
]
