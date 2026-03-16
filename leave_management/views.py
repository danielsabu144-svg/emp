from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    CASUAL_LEAVE_NAME,
    Leave,
    LeaveBalance,
    current_leave_year,
    ensure_leave_balances_for_employee,
    get_active_leave_types,
)
from chatbot.models import Notification

@login_required
def leave_requests(request):
    """View all leave requests (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'PENDING')
    
    leaves = Leave.objects.all().select_related('employee', 'leave_type', 'approved_by').order_by('-applied_on')
    
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    
    context = {
        'leaves': leaves,
        'status_filter': status_filter,
    }
    
    return render(request, 'hr/leave_requests.html', context)


@login_required
def approve_leave(request, leave_id):
    """Approve a leave request (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    leave = get_object_or_404(Leave, id=leave_id)
    
    if leave.status != 'PENDING':
        messages.warning(request, 'This leave request has already been processed.')
        return redirect('leave_requests')
    
    leave.status = 'APPROVED'
    leave.approved_by = request.user
    leave.save()
    
    # Update leave balance
    current_year = current_leave_year()
    leave_balance, created = LeaveBalance.objects.get_or_create(
        employee=leave.employee,
        leave_type=leave.leave_type,
        year=current_year,
        defaults={'total_leaves': leave.leave_type.max_days_per_year}
    )
    leave_balance.used_leaves += leave.total_days
    leave_balance.save()
    
    # Send Notification to Employee
    Notification.objects.create(
        user=leave.employee,
        notification_type='LEAVE',
        title="Leave Approved",
        message=f"Your leave request for {leave.from_date} to {leave.to_date} has been approved."
    )
    
    messages.success(request, f'Leave request approved for {leave.employee.get_full_name()}.')
    return redirect('leave_requests')


@login_required
def reject_leave(request, leave_id):
    """Reject a leave request (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    leave = get_object_or_404(Leave, id=leave_id)
    
    if leave.status != 'PENDING':
        messages.warning(request, 'This leave request has already been processed.')
        return redirect('leave_requests')
    
    if request.method == 'POST':
        leave.status = 'REJECTED'
        leave.approved_by = request.user
        leave.approval_remarks = request.POST.get('remarks', '')
        leave.save()
        
        # Send Notification to Employee
        Notification.objects.create(
            user=leave.employee,
            notification_type='LEAVE',
            title="Leave Rejected",
            message=f"Your leave request for {leave.from_date} to {leave.to_date} has been rejected. Remarks: {leave.approval_remarks}"
        )
        
        messages.success(request, f'Leave request rejected for {leave.employee.get_full_name()}.')
        return redirect('leave_requests')
    
    return render(request, 'hr/reject_leave.html', {'leave': leave})


@login_required
def my_leaves(request):
    """View employee's own leaves"""
    if request.user.is_hr:
        return redirect('leave_requests')
    
    leaves = Leave.objects.filter(employee=request.user).select_related('leave_type').order_by('-applied_on')
    
    # Get leave balances
    current_year = current_leave_year()
    ensure_leave_balances_for_employee(request.user, current_year)
    leave_balances = LeaveBalance.objects.filter(
        employee=request.user,
        year=current_year,
        leave_type__name=CASUAL_LEAVE_NAME,
        leave_type__is_active=True,
    ).select_related('leave_type')
    
    context = {
        'leaves': leaves,
        'leave_balances': leave_balances,
    }
    
    return render(request, 'employee/leaves.html', context)


@login_required
def apply_leave(request):
    """Apply for leave"""
    if request.user.is_hr:
        messages.error(request, 'HR cannot apply for leave through this form.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        leave_type_id = request.POST.get('leave_type')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')

        if not leave_type_id:
            messages.error(request, 'Please select a leave type.')
            return redirect('apply_leave')
        
        # Validate dates
        from datetime import datetime
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        if from_date_obj > to_date_obj:
            messages.error(request, 'From date cannot be after To date.')
            return redirect('apply_leave')
        
        if from_date_obj < timezone.localdate():
            messages.error(request, 'Cannot apply for past dates.')
            return redirect('apply_leave')
        
        # Create leave request
        leave_type = get_object_or_404(get_active_leave_types(), id=leave_type_id)
        
        leave = Leave.objects.create(
            employee=request.user,
            leave_type=leave_type,
            from_date=from_date_obj,
            to_date=to_date_obj,
            reason=reason,
            status='PENDING'
        )
        
        messages.success(request, 'Leave application submitted successfully.')
        return redirect('my_leaves')
    
    leave_types = get_active_leave_types()

    if not leave_types.exists():
        messages.warning(request, 'No active leave types are configured yet. Please contact HR.')
    
    context = {
        'leave_types': leave_types,
    }
    
    return render(request, 'employee/apply_leave.html', context)
