from django.test import TestCase
from rest_framework.test import APIClient

from Apps.offices.models import Office

from .models import Employee


class RegisterEmployeeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.office = Office.objects.create(name='Main Office', location='Chennai')

    def test_register_employee_requires_name(self):
        response = self.client.post(
            '/api/employees/register/',
            {
                'username': 'alex',
                'password': 'secret123',
                'phone': '9999999999',
                'office': self.office.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Full name is required.')
        self.assertFalse(Employee.objects.filter(username='alex').exists())

    def test_register_employee_successfully_creates_user(self):
        response = self.client.post(
            '/api/employees/register/',
            {
                'name': 'Alex Johnson',
                'username': 'alex',
                'password': 'secret123',
                'phone': '9999999999',
                'gender': Employee.GENDER_OTHER,
                'role': Employee.ROLE_EMPLOYEE,
                'job_role': 'Store Keeper',
                'department': 'Stores',
                'email': 'alex@example.com',
                'office': self.office.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Registration complete.')
        self.assertTrue(Employee.objects.filter(username='alex', name='Alex Johnson').exists())
