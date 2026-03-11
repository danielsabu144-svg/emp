from django import template

register = template.Library()

@register.filter
def sum_hours(work_logs):
    """Calculate total hours from work logs"""
    total = sum(log.hours_spent for log in work_logs)
    return total
