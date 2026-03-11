from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Project, Task, DailyWorkStatus
from .forms import ProjectForm, TaskForm, WorkStatusForm

@login_required
def project_list(request):
    """View all projects (Admin/HR see all, Employees see their projects)"""
    if request.user.is_hr:
        projects = Project.objects.all()
    else:
        # Get projects where employee has assigned tasks
        projects = Project.objects.filter(tasks__assigned_to=request.user).distinct()
    
    return render(request, 'task_management/project_list.html', {'projects': projects})

@login_required
def project_create(request):
    """HR/Admin can create projects"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    return render(request, 'task_management/project_form.html', {'form': form, 'title': 'Create New Project'})

@login_required
def task_create(request):
    """HR/Admin can assign tasks"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" assigned to {task.assigned_to.get_full_name()}!')
            return redirect('project_list')
    else:
        form = TaskForm()
        # Pre-select project if passed in GET
        project_id = request.GET.get('project')
        if project_id:
            form.fields['project'].initial = project_id
            
    return render(request, 'task_management/task_form.html', {'form': form, 'title': 'Assign New Task'})

@login_required
def all_tasks(request):
    """HR/Admin view all tasks with employee assignments"""
    if not request.user.is_hr:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    tasks = Task.objects.all().select_related('project', 'assigned_to').prefetch_related('work_logs').order_by('-created_at')
    
    return render(request, 'task_management/all_tasks.html', {
        'tasks': tasks,
        'today': timezone.now().date()
    })


@login_required
def my_tasks(request):
    """Employee's own tasks"""
    tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')
    return render(request, 'task_management/my_tasks.html', {'tasks': tasks})

@login_required
def task_detail(request, task_id):
    """View task details and update work status"""
    task = get_object_or_404(Task, id=task_id)
    
    # Security check: only assigned employee or HR can view
    if not request.user.is_hr and task.assigned_to != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    work_logs = task.work_logs.all()
    
    if request.method == 'POST' and task.assigned_to == request.user:
        form = WorkStatusForm(request.POST)
        if form.is_valid():
            work_log = form.save(commit=False)
            work_log.task = task
            work_log.employee = request.user
            work_log.save()
            
            # Update task status automatically
            task.status = work_log.status_update
            if task.status == 'COMPLETED':
                task.completed_at = timezone.now()
            task.save()
            
            messages.success(request, 'Work status updated successfully!')
            return redirect('task_detail', task_id=task.id)
    else:
        form = WorkStatusForm(initial={'status_update': task.status})
        
    return render(request, 'task_management/task_detail.html', {
        'task': task,
        'work_logs': work_logs,
        'form': form
    })

@login_required
def admin_task_summary(request):
    """High-level summary for the Administrator"""
    if not request.user.is_superuser:
        messages.error(request, 'Superuser privileges required.')
        return redirect('dashboard')
    
    projects = Project.objects.all()
    recent_work = DailyWorkStatus.objects.all()[:15]
    
    return render(request, 'task_management/admin_summary.html', {
        'projects': projects,
        'recent_work': recent_work
    })
