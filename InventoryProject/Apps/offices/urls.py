from django.urls import path
from .views import get_offices

urlpatterns = [
    path('', get_offices),
]