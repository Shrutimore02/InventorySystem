from django.urls import path

from .views import list_notifications


urlpatterns = [
    path('', list_notifications),
]
