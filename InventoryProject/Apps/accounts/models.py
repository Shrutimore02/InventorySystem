from django.db import models
from Apps.offices.models import Office

class Employee(models.Model):
    ROLE_EMPLOYEE = 'EMP'
    ROLE_ADMIN = 'ADM'
    ROLE_CHOICES = [
        (ROLE_EMPLOYEE, 'Employee'),
        (ROLE_ADMIN, 'Admin'),
    ]
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
    ]

    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, default='')
    phone = models.CharField(max_length=15)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    role = models.CharField(max_length=3, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    job_role = models.CharField(max_length=120, default='Employee')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default=GENDER_OTHER)
    department = models.CharField(max_length=100, default='General')
    email = models.EmailField(blank=True, default='')

    def __str__(self):
        return self.name
