from django import forms
from .models import Notification
from accounts.models import User

class NotificationForm(forms.ModelForm):
    target_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='EMPLOYEE'),
        required=False,
        label="Select Employees (Leave blank for ALL)",
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'})
    )
    
    class Meta:
        model = Notification
        fields = ['notification_type', 'title', 'message']
        widgets = {
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification Title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter notification message...'}),
        }
