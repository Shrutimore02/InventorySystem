from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item
from Apps.transfers.models import Transfer


def _get_current_assignment(item):
    return Transfer.objects.select_related('receiver', 'to_office').filter(
        item=item,
        status__in=[Transfer.STATUS_RECEIVED, Transfer.STATUS_RETURN_REQUESTED],
    ).order_by('-transfer_date', '-id').first()

@api_view(['GET'])
def get_items(request):
    items = Item.objects.order_by('name')
    data = [
        {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'item_code': item.item_code,
            'availability': item.availability,
            'total_quantity': item.total_quantity,
            'assigned_quantity': item.assigned_quantity,
            'available_quantity': item.available_quantity,
            'location_note': item.location_note,
            'qr_value': item.qr_value,
            'current_holder_id': assignment.receiver_id if assignment else None,
            'current_holder_name': assignment.receiver.name if assignment else '',
            'current_office_id': assignment.to_office_id if assignment else None,
            'current_office_name': assignment.to_office.name if assignment else '',
            'current_floor': assignment.to_floor if assignment else '',
            'current_transfer_status': assignment.status if assignment else '',
        }
        for item in items
        for assignment in [_get_current_assignment(item)]
    ]
    return Response(data)
