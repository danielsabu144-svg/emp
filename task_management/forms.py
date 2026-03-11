from django import forms
from .models import Project, Task, DailyWorkStatus
from accounts.models import User

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'client_name', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Project Description'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client Name (Optional)'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(role='EMPLOYEE')
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"

    class Meta:
        model = Task
        fields = ['project', 'assigned_to', 'title', 'description', 'priority', 'status', 'due_date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Task Description'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class WorkStatusForm(forms.ModelForm):
    class Meta:
        model = DailyWorkStatus
        fields = ['hours_spent', 'work_description', 'status_update']
        widgets = {
            'hours_spent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Hours spent today'}),
            'work_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What did you work on today?'}),
            'status_update': forms.Select(attrs={'class': 'form-control'}),
        }
