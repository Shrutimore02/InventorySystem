from django.db import models
from Apps.items.models import Item
from Apps.offices.models import Office
from Apps.accounts.models import Employee


class Transfer(models.Model):
    STATUS_AWAITING_APPROVAL = 'AWAITING_APPROVAL'
    STATUS_APPROVED = 'APPROVED'
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_RETURN_REQUESTED = 'RETURN_REQUESTED'
    STATUS_RETURNED = 'RETURNED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_AWAITING_APPROVAL, 'Awaiting Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_RETURN_REQUESTED, 'Return Requested'),
        (STATUS_RETURNED, 'Returned'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    CONDITION_GOOD = 'GOOD'
    CONDITION_DAMAGED = 'DAMAGED'
    CONDITION_INCOMPLETE = 'INCOMPLETE'
    CONDITION_CHOICES = [
        (CONDITION_GOOD, 'Good'),
        (CONDITION_DAMAGED, 'Damaged'),
        (CONDITION_INCOMPLETE, 'Incomplete'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    serial_number = models.CharField(max_length=100)
    description = models.TextField()

    from_office = models.ForeignKey(Office, related_name='from_office', on_delete=models.CASCADE)
    to_office = models.ForeignKey(Office, related_name='to_office', on_delete=models.CASCADE)
    from_floor = models.CharField(max_length=100, blank=True, default='')
    to_floor = models.CharField(max_length=100, blank=True, default='')

    sender = models.ForeignKey(Employee, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Employee, related_name='receiver', on_delete=models.CASCADE)

    transfer_date = models.DateTimeField(auto_now_add=True)
    probable_days = models.IntegerField()
    expected_date = models.DateField()

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_AWAITING_APPROVAL)

    approved_by = models.ForeignKey(
        Employee, related_name='approved_transfers', on_delete=models.SET_NULL, null=True, blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, default='')
    rejected_by = models.ForeignKey(
        Employee, related_name='rejected_transfers', on_delete=models.SET_NULL, null=True, blank=True
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
    received_date = models.DateTimeField(null=True, blank=True)
    return_requested_at = models.DateTimeField(null=True, blank=True)
    return_requested_by = models.ForeignKey(
        Employee, related_name='return_requested_transfers', on_delete=models.SET_NULL, null=True, blank=True
    )
    return_confirmed_by = models.ForeignKey(
        Employee, related_name='return_confirmed_transfers', on_delete=models.SET_NULL, null=True, blank=True
    )
    returned_date = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default=CONDITION_GOOD)
    return_note = models.TextField(blank=True, default='')


class TransferAuditLog(models.Model):
    transfer = models.ForeignKey(Transfer, related_name='audit_logs', on_delete=models.CASCADE)
    actor = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class TransferImage(models.Model):
    transfer = models.ForeignKey(Transfer, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='transfers/')


class ReturnImage(models.Model):
    transfer = models.ForeignKey(Transfer, related_name='return_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='returns/')
