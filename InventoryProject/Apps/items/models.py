import uuid

from django.db import models


def generate_item_code():
    return f"ITM-{uuid.uuid4().hex[:8].upper()}"

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('SIM', 'Simulator'),
        ('DEV', 'Device'),
        ('OTH', 'Other')
    ]
    AVAILABILITY_AVAILABLE = 'AVAILABLE'
    AVAILABILITY_ASSIGNED = 'ASSIGNED'
    AVAILABILITY_IN_APPROVAL = 'IN_APPROVAL'
    AVAILABILITY_RETURN_PENDING = 'RETURN_PENDING'
    AVAILABILITY_MAINTENANCE = 'MAINTENANCE'
    AVAILABILITY_CHOICES = [
        (AVAILABILITY_AVAILABLE, 'Available'),
        (AVAILABILITY_ASSIGNED, 'Assigned'),
        (AVAILABILITY_IN_APPROVAL, 'Awaiting Approval'),
        (AVAILABILITY_RETURN_PENDING, 'Return Pending'),
        (AVAILABILITY_MAINTENANCE, 'Maintenance'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    item_code = models.CharField(max_length=20, unique=True, default=generate_item_code)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default=AVAILABILITY_AVAILABLE)
    total_quantity = models.PositiveIntegerField(default=1)
    assigned_quantity = models.PositiveIntegerField(default=0)
    location_note = models.CharField(max_length=200, blank=True, default='')
    qr_value = models.CharField(max_length=255, blank=True, default='')

    @property
    def available_quantity(self):
        return max(self.total_quantity - self.assigned_quantity, 0)

    def __str__(self):
        return self.name


class SimulatorDetails(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    calibration_end_date = models.DateField()
