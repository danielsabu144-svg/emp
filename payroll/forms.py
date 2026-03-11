from django import forms
from .models import Payroll

class PayrollUpdateForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['allowances', 'deductions', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
