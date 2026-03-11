from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import User
from attendance.models import Attendance
from leave_management.models import LeaveBalance

from .forms import NotificationForm
from .models import ChatHistory, ChatbotResponse, Notification


@login_required
def chatbot_view(request):
    """Chatbot interface"""
    return render(request, 'chatbot/chatbot.html')


@login_required
def chatbot_api(request):
    """API endpoint for chatbot responses"""
    if request.method == 'POST':
        question = request.POST.get('question', '').lower().strip()

        if not question:
            return JsonResponse({'response': 'Please ask a question.'})

        response = get_chatbot_response(question, request.user)

        ChatHistory.objects.create(
            user=request.user,
            question=question,
            response=response
        )

        return JsonResponse({'response': response})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_chatbot_response(question, user):
    """Generate rule-based chatbot response"""

    if any(word in question for word in ['leave', 'balance', 'remaining']):
        current_year = timezone.localdate().year
        leave_balances = LeaveBalance.objects.filter(employee=user, year=current_year)

        if leave_balances.exists():
            response = "Your leave balance:\n\n"
            for balance in leave_balances:
                response += f"- {balance.leave_type.name}: {balance.remaining_leaves} days remaining\n"
            return response
        return "No leave balance information available for this year."

    if any(word in question for word in ['attendance', 'present', 'absent']):
        local_today = timezone.localdate()
        current_month = local_today.month
        current_year = local_today.year

        attendance_records = Attendance.objects.filter(
            employee=user,
            date__month=current_month,
            date__year=current_year
        )
        attendance_credit = sum(
            (record.attendance_credit for record in attendance_records),
            Decimal('0.0')
        )
        late_days = attendance_records.filter(is_late=True).count()
        early_leave_days = attendance_records.filter(is_early_leave=True).count()
        half_days = attendance_records.filter(is_half_day=True).count()
        total_days = attendance_records.count()

        return (
            "Your attendance for this month:\n\n"
            f"- Attendance credit: {attendance_credit} days\n"
            f"- Late entries: {late_days}\n"
            f"- Early leaves: {early_leave_days}\n"
            f"- Half-days: {half_days}\n"
            f"- Total records: {total_days} days"
        )

    if any(word in question for word in ['hours', 'time', 'working hours']):
        today = timezone.localdate()
        try:
            attendance = Attendance.objects.get(employee=user, date=today)
            if attendance.check_in and attendance.check_out:
                hours = attendance.get_work_hours()
                return f"Today's working hours: {hours['formatted']}"
            if attendance.check_in:
                return (
                    f"You checked in at {attendance.check_in.strftime('%I:%M %p')}. "
                    "Please check out to see total hours."
                )
            return "No attendance record found for today."
        except Attendance.DoesNotExist:
            return "You haven't marked attendance today."

    if any(word in question for word in ['salary', 'payroll', 'pay']):
        return (
            "You can view your salary details in the 'My Payroll' section. "
            "It includes your basic salary, allowances, deductions, and net salary."
        )

    if any(word in question for word in ['apply leave', 'request leave', 'take leave']):
        return (
            "To apply for leave:\n\n"
            "1. Go to 'My Leaves' section\n"
            "2. Click on 'Apply Leave'\n"
            "3. Select leave type and dates\n"
            "4. Provide reason\n"
            "5. Submit the application\n\n"
            "Your leave request will be sent to HR for approval."
        )

    if any(word in question for word in ['policy', 'policies', 'rules']):
        return (
            "HR Policies:\n\n"
            "- Working hours: 9 AM - 6 PM\n"
            "- Lunch break: 1 hour\n"
            "- Leave types: Casual, Sick, Earned\n"
            "- Attendance is mandatory\n"
            "- The system flags late entries, early exits, and half-days automatically\n\n"
            "For detailed policies, please contact HR."
        )

    if any(word in question for word in ['contact', 'hr', 'help']):
        return (
            "You can contact HR through:\n\n"
            "- Email: hr@company.com\n"
            "- Phone: +91-XXXXXXXXXX\n"
            "- Office: HR Department, 2nd Floor\n"
            "- Working hours: 9 AM - 6 PM"
        )

    if any(word in question for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
        return (
            f"Hello {user.get_full_name()}!\n\n"
            "I'm your HR assistant. I can help you with:\n\n"
            "- Leave balance\n"
            "- Attendance status\n"
            "- Salary information\n"
            "- Leave applications\n"
            "- HR policies\n"
            "- Contact information\n\n"
            "What would you like to know?"
        )

    if any(word in question for word in ['thank', 'thanks']):
        return "You're welcome! Feel free to ask if you have any other questions."

    try:
        chatbot_response = ChatbotResponse.objects.filter(
            keyword__icontains=question,
            is_active=True
        ).first()

        if chatbot_response:
            return chatbot_response.response
    except Exception:
        pass

    return (
        "I'm sorry, I didn't understand that. I can help you with:\n\n"
        "- Leave balance\n"
        "- Attendance status\n"
        "- Salary information\n"
        "- Leave applications\n"
        "- HR policies\n"
        "- Contact information\n\n"
        "Please try asking about one of these topics."
    )


@login_required
def notifications(request):
    """View all notifications"""
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()
            except Notification.DoesNotExist:
                pass

    context = {
        'notifications': user_notifications,
    }

    return render(request, 'chatbot/notifications.html', context)


@login_required
def send_notification(request):
    """Send notification (HR only)"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification_type = form.cleaned_data['notification_type']
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            target_users = form.cleaned_data['target_users']

            if not target_users:
                employees = User.objects.filter(role='EMPLOYEE')
                for emp in employees:
                    Notification.objects.create(
                        user=emp,
                        notification_type=notification_type,
                        title=title,
                        message=message
                    )
            else:
                for emp in target_users:
                    Notification.objects.create(
                        user=emp,
                        notification_type=notification_type,
                        title=title,
                        message=message
                    )

            messages.success(request, 'Notification sent successfully.')
            return redirect('notifications')
    else:
        form = NotificationForm()

    return render(request, 'hr/send_notification.html', {'form': form})
