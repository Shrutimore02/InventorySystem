from rest_framework.decorators import api_view
from rest_framework.response import Response

from Apps.accounts.models import Employee
from Apps.accounts.views import get_current_employee
from Apps.transfers.views import _sync_overdue_notifications

from .models import Notification


@api_view(['GET'])
def list_notifications(request):
    user_id = request.GET.get('user_id')
    user = Employee.objects.filter(pk=user_id).first() if user_id else get_current_employee(request)
    if not user:
        return Response([])

    _sync_overdue_notifications()
    if user.role == Employee.ROLE_ADMIN:
        notifications = Notification.objects.filter(user__role=Employee.ROLE_ADMIN).select_related('transfer', 'user').order_by('-created_at')
    else:
        notifications = Notification.objects.filter(user=user).select_related('transfer', 'user').order_by('-created_at')

    unique_notifications = []
    seen_keys = set()
    for notification in notifications:
        key = (notification.transfer_id, notification.notification_type, notification.message)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_notifications.append(notification)

    data = [
        {
            'id': notification.id,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at,
            'transfer_id': notification.transfer_id,
        }
        for notification in unique_notifications
    ]
    return Response(data)
