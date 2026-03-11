from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('tasks/', views.all_tasks, name='all_tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('admin/summary/', views.admin_task_summary, name='admin_task_summary'),
]
