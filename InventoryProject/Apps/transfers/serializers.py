from rest_framework import serializers
from django.utils import timezone
from .models import Transfer, TransferAuditLog, TransferImage, ReturnImage


class TransferImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferImage
        fields = ['image']


class ReturnImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnImage
        fields = ['image']


class TransferAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.name', read_only=True)

    class Meta:
        model = TransferAuditLog
        fields = ['action', 'note', 'actor_name', 'created_at']


class TransferSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item.name', read_only=True)
    item_category = serializers.CharField(source='item.category', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    item_availability = serializers.CharField(source='item.availability', read_only=True)
    item_total_quantity = serializers.IntegerField(source='item.total_quantity', read_only=True)
    item_assigned_quantity = serializers.IntegerField(source='item.assigned_quantity', read_only=True)
    item_available_quantity = serializers.IntegerField(source='item.available_quantity', read_only=True)
    item_qr_value = serializers.CharField(source='item.qr_value', read_only=True)
    from_office_name = serializers.CharField(source='from_office.name', read_only=True)
    to_office_name = serializers.CharField(source='to_office.name', read_only=True)
    from_location_label = serializers.SerializerMethodField()
    to_location_label = serializers.SerializerMethodField()
    sender_name = serializers.CharField(source='sender.name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True)
    return_confirmed_by_name = serializers.CharField(source='return_confirmed_by.name', read_only=True)
    rejected_by_name = serializers.CharField(source='rejected_by.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    status_description = serializers.SerializerMethodField()

    images = TransferImageSerializer(many=True, read_only=True)
    return_images = ReturnImageSerializer(many=True, read_only=True)
    audit_logs = TransferAuditLogSerializer(many=True, read_only=True)

    def get_is_overdue(self, obj):
        return bool(
            obj.expected_date and obj.expected_date < timezone.localdate()
            and obj.status not in [Transfer.STATUS_RETURNED, Transfer.STATUS_CANCELLED]
        )

    def get_status_description(self, obj):
        descriptions = {
            Transfer.STATUS_AWAITING_APPROVAL: 'Waiting for an admin to approve the transfer request.',
            Transfer.STATUS_APPROVED: 'Approved by admin. The receiver can now confirm the item after it arrives.',
            Transfer.STATUS_RECEIVED: 'The receiver confirmed the item has arrived and is currently using it.',
            Transfer.STATUS_RETURN_REQUESTED: 'The receiver sent the item back and is waiting for an admin to confirm the return.',
            Transfer.STATUS_RETURNED: 'The return is fully completed and confirmed by admin.',
            Transfer.STATUS_CANCELLED: 'The transfer request was cancelled before completion.',
            Transfer.STATUS_REJECTED: 'The transfer request was rejected by an admin.',
        }
        return descriptions.get(obj.status, '')

    def get_from_location_label(self, obj):
        return self._build_location_label(obj.from_office.name, obj.from_floor)

    def get_to_location_label(self, obj):
        return self._build_location_label(obj.to_office.name, obj.to_floor)

    @staticmethod
    def _build_location_label(office_name, floor_name):
        if floor_name:
            return f"{office_name} - {floor_name}"
        return office_name

    class Meta:
        model = Transfer
        fields = '__all__'
