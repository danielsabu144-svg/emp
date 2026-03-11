from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from attendance.models import Attendance

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"LOGIN_DEBUG: Attempting login for '{username}'")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"LOGIN_DEBUG: Authentication successful for '{username}'")
            auth_login(request, user)
            
            if user.is_employee:
                today = timezone.localdate()
                existing_attendance = Attendance.objects.filter(employee=user, date=today).first()
                if existing_attendance and existing_attendance.check_in and not existing_attendance.check_out:
                    messages.info(
                        request,
                        f'Welcome back! You are already checked in for {today}.'
                    )
                elif existing_attendance and existing_attendance.check_out:
                    messages.info(
                        request,
                        f'Welcome back! Your attendance for {today} is already closed.'
                    )
                else:
                    messages.success(
                        request,
                        'Welcome back! Use the Check In button on your dashboard to mark attendance.'
                    )
            else:
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            print(f"LOGIN_DEBUG: Redirecting '{username}' to dashboard")
            return redirect('dashboard')
        else:
            print(f"LOGIN_DEBUG: Authentication failed for '{username}'")
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """Handle user logout"""
    # Update logout time for attendance
    if request.user.is_employee:
        current_time = timezone.localtime(timezone.now())
        today = current_time.date()
        try:
            attendance = Attendance.objects.get(employee=request.user, date=today)
            if not attendance.check_out:
                attendance.check_out = current_time.time()
                attendance.save(update_fields=['check_out'])
        except Attendance.DoesNotExist:
            pass
    
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard - redirects to appropriate dashboard based on role"""
    if request.user.is_hr:
        return redirect('hr_dashboard')
    else:
        return redirect('employee_dashboard')
