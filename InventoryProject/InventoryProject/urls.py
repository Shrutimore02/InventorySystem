from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

from Apps.accounts.views import admin_required_view, get_current_employee, login_page, login_required_view, logout_page, register_page

from django.conf import settings
from django.conf.urls.static import static


@login_required_view
def dashboard(request):
    return render(request, 'dashboard.html', {'current_employee': request.current_employee, 'page_title': 'Dashboard'})

@login_required_view
def create_transfer(request):
    return render(request, 'create_transfer.html', {'current_employee': request.current_employee, 'page_title': 'Transfer'})

@login_required_view
def history_page(request):
    return render(request, 'history.html', {'current_employee': request.current_employee, 'page_title': 'History'})


@admin_required_view
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html', {'current_employee': request.current_employee, 'page_title': 'Admin Dashboard'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard),
    path('admin-panel/', admin_dashboard),
    path('create/', create_transfer),
    path('history/', history_page),
    path('login/', login_page),
    path('register/', register_page),
    path('logout/', logout_page),

    path('api/transfers/', include('Apps.transfers.urls')),
    path('api/offices/', include('Apps.offices.urls')),
    path('api/items/', include('Apps.items.urls')),
    path('api/employees/', include('Apps.accounts.urls')),
    path('api/notifications/', include('Apps.notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
