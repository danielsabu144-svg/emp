from django.urls import path
from . import views

urlpatterns = [
    # HR views
    path('list/', views.payroll_list, name='payroll_list'),
    path('generate/', views.generate_payroll, name='generate_payroll'),
    path('detail/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
    path('mark-paid/<int:payroll_id>/', views.mark_as_paid, name='mark_as_paid'),
    path('update/<int:payroll_id>/', views.update_payroll, name='update_payroll'),
    
    # Employee views
    path('my/', views.my_payroll, name='my_payroll'),
]
