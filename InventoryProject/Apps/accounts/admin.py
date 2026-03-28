from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from .models import Employee


class EmployeeAdminForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text='Enter a password for this employee login.',
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    class Meta:
        model = Employee
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['password'].help_text = 'Leave blank to keep the current password.'

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password') or ''
        confirm_password = cleaned_data.get('confirm_password') or ''

        if self.instance and self.instance.pk:
            if password and password != confirm_password:
                self.add_error('confirm_password', 'Password and confirm password must match.')
        else:
            if not password:
                self.add_error('password', 'Password is required.')
            if password != confirm_password:
                self.add_error('confirm_password', 'Password and confirm password must match.')

        return cleaned_data

    def save(self, commit=True):
        employee = super().save(commit=False)
        password = self.cleaned_data.get('password') or ''
        if password:
            employee.password = make_password(password)
        if commit:
            employee.save()
            self.save_m2m()
        return employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = ('name', 'username', 'role', 'department', 'office', 'phone')
    search_fields = ('name', 'username', 'phone', 'department')
    list_filter = ('role', 'gender', 'office')
    readonly_fields = ('password_preview',)
    fieldsets = (
        ('Employee Details', {
            'fields': (
                'name', 'username', 'role', 'office', 'phone',
                'job_role', 'department', 'email', 'gender',
            ),
        }),
        ('Login Credentials', {
            'fields': ('password', 'confirm_password', 'password_preview'),
        }),
    )
    add_fieldsets = (
        ('Employee Details', {
            'fields': (
                'name', 'username', 'role', 'office', 'phone',
                'job_role', 'department', 'email', 'gender',
            ),
        }),
        ('Login Credentials', {
            'fields': ('password', 'confirm_password'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    @admin.display(description='Stored Password')
    def password_preview(self, obj):
        if not obj or not obj.password:
            return '-'
        return 'Password is stored securely and cannot be shown.'
