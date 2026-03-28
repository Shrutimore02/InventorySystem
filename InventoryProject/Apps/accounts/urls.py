from django.urls import path
from .views import current_user, list_employees, login_employee, register_employee

urlpatterns = [
    path('', list_employees),
    path('me/', current_user),
    path('login/', login_employee),
    path('register/', register_employee),
]
