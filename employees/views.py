from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.views.decorators.http import require_POST
from .forms import UserForm, EmployeeProfileForm
from accounts.models import User as CustomUser
from datetime import datetime, timedelta
from accounts.models import User
from .models import EmployeeProfile
from attendance.models import Attendance
from leave_management.models import Leave, LeaveBalance, ensure_leave_balances_for_employee
from payroll.models import Payroll
from chatbot.models import Notification


def can_delete_user(current_user, target_user):
    if current_user == target_user:
        return False
    if current_user.is_superuser:
        return not target_user.is_superuser
    return current_user.is_hr and target_user.role == 'EMPLOYEE'


@login_required
def hr_dashboard(request):
    """HR/Admin Dashboard with statistics and charts"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied. HR privileges required.')
        return redirect('employee_dashboard')
    
    # Get statistics
    if request.user.is_superuser:
        total_employees = User.objects.all().count()
        total_hr = User.objects.filter(role='HR').count()
    else:
        total_employees = User.objects.filter(role='EMPLOYEE').count()
        total_hr = 0
    today = timezone.localdate()
    
    # Today's attendance
    present_today = Attendance.objects.filter(date=today).filter(Attendance.payable_query()).count()
    absent_today = total_employees - present_today
    
    # Pending leave requests
    pending_leaves = Leave.objects.filter(status='PENDING').count()
    
    # This month's payroll
    current_month = today.month
    current_year = today.year
    payroll_generated = Payroll.objects.filter(month=current_month, year=current_year).count()
    
    # Project & Task stats
    from task_management.models import Project, Task
    active_projects = Project.objects.filter(status='ONGOING').count()
    pending_tasks = Task.objects.exclude(status='COMPLETED').count()
    
    # Recent employees
    recent_employees = User.objects.filter(role='EMPLOYEE').order_by('-date_joined')[:5]
    
    # Pending leave requests
    pending_leave_requests = Leave.objects.filter(status='PENDING').select_related('employee', 'leave_type')[:5]
    
    # Upcoming birthdays (next 7 days)
    today_date = today
    upcoming_birthdays = []
    employees = User.objects.filter(role='EMPLOYEE', date_of_birth__isnull=False)
    for emp in employees:
        birthday_this_year = emp.date_of_birth.replace(year=today_date.year)
        if birthday_this_year < today_date:
            birthday_this_year = emp.date_of_birth.replace(year=today_date.year + 1)
        days_until = (birthday_this_year - today_date).days
        if 0 <= days_until <= 7:
            upcoming_birthdays.append({
                'employee': emp,
                'days_until': days_until,
                'date': birthday_this_year
            })
    
    # Department-wise employee count
    departments = EmployeeProfile.objects.values('department').annotate(count=Count('id'))
    
    # Monthly attendance trend (last 6 months)
    attendance_trend = []
    for i in range(5, -1, -1):
        date = today - timedelta(days=i*30)
        month_attendance = Attendance.objects.filter(
            date__month=date.month,
            date__year=date.year,
        ).filter(Attendance.payable_query()).count()
        attendance_trend.append({
            'month': date.strftime('%b'),
            'count': month_attendance
        })
    
    context = {
        'total_employees': total_employees,
        'total_hr': total_hr,
        'present_today': present_today,
        'absent_today': absent_today,
        'pending_leaves': pending_leaves,
        'payroll_generated': payroll_generated,
        'recent_employees': recent_employees,
        'pending_leave_requests': pending_leave_requests,
        'upcoming_birthdays': upcoming_birthdays,
        'departments': departments,
        'attendance_trend': attendance_trend,
        'active_projects': active_projects,
        'pending_tasks': pending_tasks,
    }
    
    return render(request, 'hr/dashboard.html', context)


@login_required
def employee_dashboard(request):
    """Employee Dashboard"""
    if request.user.is_hr:
        return redirect('hr_dashboard')
    
    # Get employee's data
    today = timezone.localdate()
    
    # Today's attendance
    try:
        today_attendance = Attendance.objects.get(employee=request.user, date=today)
    except Attendance.DoesNotExist:
        today_attendance = None
    
    # Leave balance
    current_year = today.year
    ensure_leave_balances_for_employee(request.user, current_year)
    leave_balances = list(
        LeaveBalance.objects.filter(employee=request.user, year=current_year)
        .select_related('leave_type')
        .order_by('leave_type__name')
    )
    total_remaining_leaves = sum(balance.remaining_leaves for balance in leave_balances)
    
    # Recent leaves
    recent_leaves = Leave.objects.filter(employee=request.user).order_by('-applied_on')[:5]
    
    # This month's attendance
    current_month = today.month
    month_attendance = Attendance.objects.filter(
        employee=request.user,
        date__month=current_month,
        date__year=current_year
    )
    present_days = sum(
        (record.attendance_credit for record in month_attendance),
        Decimal('0.0')
    )
    total_days = month_attendance.count()
    
    # Latest payroll
    try:
        latest_payroll = Payroll.objects.filter(employee=request.user).latest('year', 'month')
    except Payroll.DoesNotExist:
        latest_payroll = None
    
    # Tasks
    from task_management.models import Task
    pending_tasks = Task.objects.filter(assigned_to=request.user).exclude(status='COMPLETED').count()
    
    # Notifications
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    context = {
        'today_attendance': today_attendance,
        'leave_balances': leave_balances,
        'total_remaining_leaves': total_remaining_leaves,
        'recent_leaves': recent_leaves,
        'present_days': present_days,
        'total_days': total_days,
        'latest_payroll': latest_payroll,
        'notifications': notifications,
        'pending_tasks': pending_tasks,
    }
    
    return render(request, 'employee/dashboard.html', context)


@login_required
def employee_list(request):
    """List all employees (HR only)"""
    if request.user.is_superuser:
        # Superuser sees everyone
        employees = User.objects.all().select_related('profile').order_by('-date_joined')
    else:
        # HR only sees employees
        employees = User.objects.filter(role='EMPLOYEE').select_related('profile').order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )

    employees = list(employees)
    for employee in employees:
        employee.can_be_deleted = can_delete_user(request.user, employee)
    
    context = {
        'employees': employees,
        'search_query': search_query,
    }
    
    return render(request, 'hr/employee_list.html', context)


@login_required
def employee_detail(request, employee_id):
    """View employee details"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    # Get employee statistics (if they have a profile/attendance)
    local_today = timezone.localdate()
    current_month = local_today.month
    current_year = local_today.year
    
    month_attendance = Attendance.objects.filter(
        employee=employee,
        date__month=current_month,
        date__year=current_year
    )
    
    context = {
        'employee': employee,
        'has_profile': hasattr(employee, 'profile'),
        'month_attendance': month_attendance,
        'can_delete_employee': can_delete_user(request.user, employee),
    }
    
    return render(request, 'hr/employee_detail.html', context)


@login_required
def add_employee(request):
    """Custom Admin view to add a new employee or HR user"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        profile_form = EmployeeProfileForm(request.POST, request.FILES)
        user_role = request.POST.get('role', 'EMPLOYEE')
        
        is_user_valid = user_form.is_valid()
        is_profile_valid = profile_form.is_valid()
        
        if user_role == 'EMPLOYEE':
            if is_user_valid and is_profile_valid:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
                
                messages.success(request, f'Employee {user.get_full_name()} added successfully!')
                return redirect('employee_list')
        else:
            if is_user_valid:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                messages.success(request, f'HR Manager {user.get_full_name()} added successfully!')
                return redirect('employee_list')
                
        # DEBUG: Write errors to a file because USER doesn't see them
        with open('form_debug.log', 'w') as f:
            f.write(f"Role: {user_role}\n")
            f.write(f"User Valid: {is_user_valid}\n")
            f.write(f"User Errors: {user_form.errors.as_json()}\n")
            if user_role == 'EMPLOYEE':
                f.write(f"Profile Valid: {is_profile_valid}\n")
                f.write(f"Profile Errors: {profile_form.errors.as_json()}\n")
            
        messages.error(request, 'Please correct the errors highlighted below.')
    else:
        user_form = UserForm()
        profile_form = EmployeeProfileForm()
        
    return render(request, 'hr/employee_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Add New User (HR/Employee)'
    })

@login_required
def edit_employee(request, employee_id):
    """Custom Admin view to edit employee details"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    profile = getattr(employee, 'profile', None)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=employee)
        profile_form = EmployeeProfileForm(request.POST, instance=profile)
        
        # Password isn't required when editing unless changed
        user_form.fields['password'].required = False
        
        if user_form.is_valid():
            user = user_form.save(commit=False)
            if user_form.cleaned_data.get('password'):
                user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            # Save profile only if it exists or if role is EMPLOYEE
            if user.role == 'EMPLOYEE':
                if profile_form.is_valid():
                    p = profile_form.save(commit=False)
                    p.user = user
                    p.save()
            
            messages.success(request, f'Account for {user.get_full_name()} updated successfully!')
            return redirect('employee_list')
    else:
        user_form = UserForm(instance=employee)
        profile_form = EmployeeProfileForm(instance=profile)
        
    return render(request, 'hr/employee_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': f'Edit Employee: {employee.get_full_name()}'
    })

@login_required
def deactivate_employee(request, employee_id):
    """Toggle employee active status"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    employee = get_object_or_404(User, id=employee_id)
    
    # Toggle user's active status
    employee.is_active = not employee.is_active
    employee.save()
    
    # Toggle profile status if it exists
    if hasattr(employee, 'profile'):
        profile = employee.profile
        profile.is_active = employee.is_active
        profile.save()
    
    status = "activated" if employee.is_active else "deactivated"
    messages.success(request, f'Account for {employee.get_full_name()} has been {status}.')
    return redirect('employee_list')


@login_required
@require_POST
def delete_employee(request, employee_id):
    """Delete an employee account and cascaded profile records"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    employee = get_object_or_404(User, id=employee_id)

    if employee == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('employee_list')

    if employee.is_superuser:
        messages.error(request, 'Superadmin accounts cannot be deleted from this dashboard.')
        return redirect('employee_list')

    if not can_delete_user(request.user, employee):
        messages.error(request, 'Only employee accounts can be deleted from this dashboard.')
        return redirect('employee_list')

    employee_name = employee.get_full_name() or employee.username

    with transaction.atomic():
        employee.delete()

    messages.success(request, f'Employee profile for {employee_name} was deleted successfully.')
    return redirect('employee_list')


@login_required
def my_profile(request):
    """Employee's own profile view"""
    if request.user.is_hr:
        return redirect('hr_dashboard')
    
    return render(request, 'employee/profile.html')
