from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Attendance
from accounts.models import User

@login_required
@require_POST
def mark_attendance_checkin(request):
    """Mark check-in time for today's attendance."""
    if request.user.role != 'EMPLOYEE':
        messages.error(request, 'Only employees can mark attendance.')
        return redirect('dashboard')

    current_time = timezone.localtime(timezone.now())
    today = current_time.date()
    attendance, created = Attendance.objects.get_or_create(
        employee=request.user,
        date=today,
        defaults={'check_in': current_time.time()}
    )

    if created or not attendance.check_in:
        attendance.check_in = current_time.time()
        attendance.check_out = None
        attendance.save(update_fields=['check_in', 'check_out'])
        suffix = ''
        if attendance.detection_labels:
            suffix = f" Flags: {', '.join(attendance.detection_labels)}."
        messages.success(
            request,
            f'Checked in successfully at {attendance.check_in.strftime("%I:%M %p")}.{suffix}'
        )
    elif attendance.check_out:
        messages.info(request, 'Your attendance for today is already completed.')
    else:
        messages.info(
            request,
            f'You are already checked in since {attendance.check_in.strftime("%I:%M %p")}.'
        )

    return redirect('dashboard')


@login_required
def attendance_list(request):
    """View all attendance records (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    date_filter = request.GET.get('date', '')
    employee_filter = request.GET.get('employee', '')
    status_filter = request.GET.get('status', '')
    detection_filter = request.GET.get('detection', '')
    
    attendances = Attendance.objects.all().select_related('employee').order_by('-date', 'employee__username')
    
    # Apply filters
    if date_filter:
        attendances = attendances.filter(date=date_filter)
    if employee_filter:
        attendances = attendances.filter(employee__id=employee_filter)
    if status_filter:
        attendances = attendances.filter(Attendance.status_query(status_filter))
    if detection_filter == 'LATE':
        attendances = attendances.filter(is_late=True)
    elif detection_filter == 'EARLY_LEAVE':
        attendances = attendances.filter(is_early_leave=True)
    elif detection_filter == 'HALF_DAY':
        attendances = attendances.filter(is_half_day=True)
    
    # Get all employees for filter dropdown
    employees = User.objects.filter(role='EMPLOYEE').order_by('username')
    total_records = attendances.count()
    local_today = timezone.localdate()

    context = {
        'attendances': attendances,
        'employees': employees,
        'date_filter': date_filter,
        'employee_filter': employee_filter,
        'status_filter': status_filter,
        'detection_filter': detection_filter,
        'total_records': total_records,
        'late_entry_count': attendances.filter(is_late=True).count(),
        'early_leave_count': attendances.filter(is_early_leave=True).count(),
        'half_day_count': attendances.filter(is_half_day=True).count(),
        'today': local_today,
    }
    
    return render(request, 'hr/attendance_list.html', context)


@login_required
def my_attendance(request):
    """View employee attendance history."""
    if request.user.is_hr:
        return redirect('attendance_list')
    
    # Get month and year from query params or use current
    local_today = timezone.localdate()
    month = request.GET.get('month', local_today.month)
    year = request.GET.get('year', local_today.year)
    
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        month = local_today.month
        year = local_today.year
    
    attendances = Attendance.objects.filter(
        employee=request.user,
        date__month=month,
        date__year=year
    ).order_by('-date')
    
    # Calculate statistics
    total_days = attendances.count()
    present_days = attendances.filter(Attendance.full_day_query()).count()
    absent_days = attendances.filter(is_absent=True).count()
    late_days = attendances.filter(is_late=True).count()
    early_leave_days = attendances.filter(is_early_leave=True).count()
    half_days = attendances.filter(is_half_day=True).count()
    
    context = {
        'attendances': attendances,
        'month': month,
        'year': year,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'early_leave_days': early_leave_days,
        'half_days': half_days,
    }
    
    return render(request, 'employee/attendance.html', context)

@login_required
@require_POST
def mark_attendance_logout(request):
    """Mark check-out time for today's attendance."""
    if request.user.role != 'EMPLOYEE':
        messages.error(request, 'Only employees can mark attendance.')
        return redirect('dashboard')
    
    today = timezone.localdate()
    try:
        attendance = Attendance.objects.get(employee=request.user, date=today)
        if not attendance.check_out:
            attendance.check_out = timezone.localtime(timezone.now()).time()
            attendance.save(update_fields=['check_out'])
            suffix = ''
            if attendance.detection_labels:
                suffix = f" Flags: {', '.join(attendance.detection_labels)}."
            messages.success(
                request,
                f'Attendance closed successfully at {attendance.check_out.strftime("%I:%M %p")}.{suffix}'
            )
        else:
            messages.info(request, 'You have already marked your check-out time for today.')
    except Attendance.DoesNotExist:
        messages.error(request, 'No check-in record found for today. Please check in first.')
    
    return redirect('dashboard')
