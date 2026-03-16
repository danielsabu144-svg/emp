from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.views.decorators.http import require_POST
from .models import Payroll
from accounts.models import User
from chatbot.models import Notification
from attendance.models import Attendance
from employees.models import EmployeeProfile
import calendar
from .forms import PayrollUpdateForm


def get_payroll_period_options():
    today = timezone.localdate()
    months = list(enumerate(calendar.month_name))[1:]
    years = list(range(today.year - 2, today.year + 3))
    return months, years


def normalize_payroll_period(month_value, year_value):
    today = timezone.localdate()
    try:
        month = int(month_value)
        year = int(year_value)
    except (TypeError, ValueError):
        return today.month, today.year, False

    if not 1 <= month <= 12:
        return today.month, today.year, False
    if year < 2000 or year > 9999:
        return today.month, today.year, False
    return month, year, True

@login_required
def payroll_list(request):
    """View all payroll records (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    local_today = timezone.localdate()
    month_filter, year_filter, is_valid_period = normalize_payroll_period(
        request.GET.get('month', local_today.month),
        request.GET.get('year', local_today.year),
    )
    if request.GET and not is_valid_period:
        messages.warning(request, 'Invalid payroll period selected. Showing the current month instead.')
    
    payrolls = Payroll.objects.filter(
        month=month_filter,
        year=year_filter
    ).select_related('employee').order_by('employee__username')
    months, years = get_payroll_period_options()
    
    context = {
        'payrolls': payrolls,
        'month': month_filter,
        'year': year_filter,
        'month_name': calendar.month_name[month_filter],
        'months': months,
        'years': years,
    }
    
    return render(request, 'hr/payroll_list.html', context)


@login_required
def generate_payroll(request):
    """Generate payroll for a specific month (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    months, years = get_payroll_period_options()
    current_month, current_year, _ = normalize_payroll_period(
        request.POST.get('month', timezone.localdate().month),
        request.POST.get('year', timezone.localdate().year),
    )

    if request.method == 'POST':
        month, year, is_valid_period = normalize_payroll_period(
            request.POST.get('month'),
            request.POST.get('year'),
        )
        if not is_valid_period:
            messages.error(request, 'Please select a valid payroll month and year.')
            return render(
                request,
                'hr/generate_payroll.html',
                {
                    'months': months,
                    'years': years,
                    'month': current_month,
                    'year': current_year,
                },
                status=400,
            )
        
        # Get all employees
        employees = User.objects.filter(role='EMPLOYEE').select_related('profile')
        
        generated_count = 0
        
        for employee in employees:
            try:
                profile = employee.profile
                
                # Check if payroll already exists
                payroll, created = Payroll.objects.get_or_create(
                    employee=employee,
                    month=month,
                    year=year,
                    defaults={
                        'basic_salary': profile.salary,
                        'working_days': 0,
                        'present_days': 0,
                        'net_salary': 0
                    }
                )
                
                if created:
                    # Calculate working days and present days
                    total_days_in_month = calendar.monthrange(year, month)[1]
                    payroll.working_days = total_days_in_month
                    
                    # Count present days
                    attendance_records = Attendance.objects.filter(
                        employee=employee,
                        date__month=month,
                        date__year=year,
                    )
                    present_days = sum(
                        (record.attendance_credit for record in attendance_records),
                        Decimal('0.0')
                    )
                    
                    payroll.present_days = present_days
                    
                    # Calculate net salary
                    payroll.calculate_net_salary()
                    payroll.save()
                    
                    # Notify Employee
                    Notification.objects.create(
                        user=employee,
                        notification_type='PAYROLL',
                        title="Salary Slip Generated",
                        message=f"Your salary slip for {calendar.month_name[month]} {year} has been generated. You can view it in the 'My Payroll' section."
                    )
                    
                    generated_count += 1
            
            except EmployeeProfile.DoesNotExist:
                continue
        
        messages.success(request, f'Payroll generated for {generated_count} employees.')
        return redirect('payroll_list')
    
    return render(
        request,
        'hr/generate_payroll.html',
        {
            'months': months,
            'years': years,
            'month': current_month,
            'year': current_year,
        },
    )


@login_required
def payroll_detail(request, payroll_id):
    """View payroll details"""
    payroll = get_object_or_404(Payroll, id=payroll_id)
    
    # Check access
    if not request.user.is_hr and payroll.employee != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    context = {
        'payroll': payroll,
    }
    
    return render(request, 'payroll/payroll_detail.html', context)

@login_required
def my_payroll(request):
    """View employee's own payroll"""
    if request.user.is_hr:
        return redirect('payroll_list')
    
    payrolls = Payroll.objects.filter(employee=request.user).order_by('-year', '-month')
    
    context = {
        'payrolls': payrolls,
    }
    
    return render(request, 'employee/payroll.html', context)


@login_required
@require_POST
def mark_as_paid(request, payroll_id):
    """Mark a payroll record as paid (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    payroll = get_object_or_404(Payroll, id=payroll_id)
    if payroll.is_paid:
        messages.info(request, f'Payroll for {payroll.employee.get_full_name()} is already marked as paid.')
        return redirect('payroll_detail', payroll_id=payroll.id)

    payroll.is_paid = True
    payroll.payment_date = timezone.localdate()
    payroll.save()
    
    messages.success(request, f'Payroll for {payroll.employee.get_full_name()} marked as paid.')
    return redirect('payroll_detail', payroll_id=payroll.id)


@login_required
def update_payroll(request, payroll_id):
    """Update payroll allowances and deductions (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    payroll = get_object_or_404(Payroll, id=payroll_id)
    
    if request.method == 'POST':
        form = PayrollUpdateForm(request.POST, instance=payroll)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.calculate_net_salary()
            payroll.save()
            messages.success(request, 'Payroll values updated successfully.')
            return redirect('payroll_detail', payroll_id=payroll.id)
    else:
        form = PayrollUpdateForm(instance=payroll)
    
    context = {
        'form': form,
        'payroll': payroll
    }
    return render(request, 'hr/update_payroll.html', context)
