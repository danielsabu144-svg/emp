from django.db import models
from accounts.models import User
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = (
        ('PLANNING', 'Planning'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    client_name = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status='COMPLETED').count()
        return int((completed / total) * 100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class Task(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('REVIEW', 'Under Review'),
        ('COMPLETED', 'Completed'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username}"

    class Meta:
        ordering = ['due_date', '-priority']

class DailyWorkStatus(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='work_logs')
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    hours_spent = models.DecimalField(max_digits=4, decimal_places=2)
    work_description = models.TextField()
    status_update = models.CharField(max_length=20, choices=Task.STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} - {self.task.title} - {self.date}"

    class Meta:
        verbose_name_plural = "Daily Work Statuses"
        ordering = ['-date', '-created_at']
