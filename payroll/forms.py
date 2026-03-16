from decimal import Decimal

from django import forms

from .models import Payroll

class PayrollUpdateForm(forms.ModelForm):
    allowances = forms.DecimalField(min_value=Decimal('0.00'), decimal_places=2, max_digits=10)
    deductions = forms.DecimalField(min_value=Decimal('0.00'), decimal_places=2, max_digits=10)

    class Meta:
        model = Payroll
        fields = ['allowances', 'deductions', 'remarks']
        widgets = {
            'allowances': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'deductions': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
