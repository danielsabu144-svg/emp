from django.urls import path
from . import views

urlpatterns = [
    # HR Dashboard
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    
    # Employee Management (HR)
    path('list/', views.employee_list, name='employee_list'),
    path('add/', views.add_employee, name='add_employee'),
    path('edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('deactivate/<int:employee_id>/', views.deactivate_employee, name='deactivate_employee'),
    path('delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    path('detail/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    
    # Employee Dashboard
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.my_profile, name='my_profile'),
]
