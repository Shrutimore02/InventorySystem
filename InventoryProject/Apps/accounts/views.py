from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect, render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from Apps.offices.models import Office

from .models import Employee


SESSION_KEY = 'employee_id'


def get_current_employee(request):
    employee_id = request.session.get(SESSION_KEY)
    if not employee_id:
        return None
    return Employee.objects.select_related('office').filter(pk=employee_id).first()


def get_post_login_redirect(employee):
    if employee and employee.role == Employee.ROLE_ADMIN:
        return '/admin-panel/'
    return '/'


def login_required_view(view_func):
    def wrapped(request, *args, **kwargs):
        employee = get_current_employee(request)
        if not employee:
            return redirect('/login/')
        request.current_employee = employee
        return view_func(request, *args, **kwargs)
    return wrapped


def admin_required_view(view_func):
    def wrapped(request, *args, **kwargs):
        employee = get_current_employee(request)
        if not employee:
            return redirect('/login/')
        if employee.role != Employee.ROLE_ADMIN:
            return redirect('/')
        request.current_employee = employee
        return view_func(request, *args, **kwargs)
    return wrapped


def serialize_employee(employee):
    return {
        'id': employee.id,
        'name': employee.name,
        'username': employee.username,
        'phone': employee.phone,
        'office': employee.office_id,
        'office_name': employee.office.name,
        'role': employee.role,
        'job_role': employee.job_role,
        'gender': employee.gender,
        'department': employee.department,
        'email': employee.email,
    }


def login_page(request):
    employee = get_current_employee(request)
    if employee:
        return redirect(get_post_login_redirect(employee))
    return render(request, 'login.html')


def register_page(request):
    employee = get_current_employee(request)
    if employee:
        return redirect(get_post_login_redirect(employee))
    offices = Office.objects.order_by('name')
    return render(request, 'register.html', {'offices': offices})


def logout_page(request):
    request.session.flush()
    return redirect('/login/')


@api_view(['GET'])
def current_user(request):
    employee = get_current_employee(request)
    if not employee:
        return Response({'authenticated': False})
    return Response({'authenticated': True, 'user': serialize_employee(employee)})


@api_view(['POST'])
def login_employee(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    employee = Employee.objects.select_related('office').filter(username=username).first()
    if not employee or not check_password(password, employee.password):
        return Response({'message': 'Invalid username or password.'}, status=400)

    request.session[SESSION_KEY] = employee.id
    return Response({
        'message': 'Login successful.',
        'user': serialize_employee(employee),
        'redirect_url': get_post_login_redirect(employee),
    })


@api_view(['POST'])
def register_employee(request):
    name = (request.data.get('name') or '').strip()
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    phone = (request.data.get('phone') or '').strip()
    office_id = request.data.get('office')
    role = request.data.get('role') or Employee.ROLE_EMPLOYEE
    job_role = (request.data.get('job_role') or 'Employee').strip()
    department = (request.data.get('department') or 'General').strip()
    email = (request.data.get('email') or '').strip()

    if not name:
        return Response({'message': 'Full name is required.'}, status=400)

    if not username:
        return Response({'message': 'Username is required.'}, status=400)

    if not password:
        return Response({'message': 'Password is required.'}, status=400)

    if not phone:
        return Response({'message': 'Phone number is required.'}, status=400)

    if Employee.objects.filter(username=username).exists():
        return Response({'message': 'This username is already taken.'}, status=400)

    office = Office.objects.filter(pk=office_id).first()
    if not office:
        return Response({'message': 'Please select a valid office.'}, status=400)

    current_employee = get_current_employee(request)
    admin_exists = Employee.objects.filter(role=Employee.ROLE_ADMIN).exists()
    if role == Employee.ROLE_ADMIN and admin_exists and (not current_employee or current_employee.role != Employee.ROLE_ADMIN):
        role = Employee.ROLE_EMPLOYEE

    employee = Employee.objects.create(
        name=name,
        username=username,
        password=make_password(password),
        phone=phone,
        office=office,
        role=role,
        job_role=job_role,
        gender=request.data.get('gender') or Employee.GENDER_OTHER,
        department=department,
        email=email,
    )

    request.session[SESSION_KEY] = employee.id
    return Response({
        'message': 'Registration complete.',
        'user': serialize_employee(employee),
        'redirect_url': get_post_login_redirect(employee),
    })


@api_view(['GET'])
def list_employees(request):
    q = request.GET.get('q', '').strip()
    employees = Employee.objects.select_related('office').order_by('name')
    if q:
        employees = employees.filter(name__icontains=q)

    return Response([serialize_employee(employee) for employee in employees])
