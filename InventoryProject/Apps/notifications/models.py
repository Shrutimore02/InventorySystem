# Apps/notifications/models.py

from django.db import models
from Apps.accounts.models import Employee
from Apps.transfers.models import Transfer

class Notification(models.Model):
    TYPE_TRANSFER_REQUEST = 'TRANSFER_REQUEST'
    TYPE_TRANSFER_APPROVED = 'TRANSFER_APPROVED'
    TYPE_RETURN_REQUEST = 'RETURN_REQUEST'
    TYPE_OVERDUE = 'OVERDUE'
    TYPE_CHOICES = [
        (TYPE_TRANSFER_REQUEST, 'Transfer Request'),
        (TYPE_TRANSFER_APPROVED, 'Transfer Approved'),
        (TYPE_RETURN_REQUEST, 'Return Request'),
        (TYPE_OVERDUE, 'Overdue'),
    ]

    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_TRANSFER_REQUEST)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
