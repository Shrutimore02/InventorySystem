import csv

from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from Apps.accounts.models import Employee
from Apps.accounts.views import get_current_employee
from Apps.items.models import Item
from Apps.notifications.models import Notification
from Apps.offices.models import Office

from .models import ReturnImage, Transfer, TransferAuditLog, TransferImage
from .serializers import TransferSerializer


def _get_actor(request):
    actor_id = request.headers.get('X-Employee-Id') or request.data.get('actor_id') or request.query_params.get('actor_id')
    if actor_id:
        try:
            return Employee.objects.get(pk=actor_id)
        except Employee.DoesNotExist:
            return None
    return get_current_employee(request)


def _admin_users():
    return Employee.objects.filter(role=Employee.ROLE_ADMIN)


def _is_admin(user):
    return bool(user and user.role == Employee.ROLE_ADMIN)


def _notification_exists(user, transfer, notification_type):
    return Notification.objects.filter(
        user=user,
        transfer=transfer,
        notification_type=notification_type,
    ).exists()


def _create_notifications(users, transfer, notification_type, message):
    for user in users:
        if not _notification_exists(user, transfer, notification_type):
            Notification.objects.create(
                user=user,
                transfer=transfer,
                notification_type=notification_type,
                message=message,
            )


def _clear_notifications(transfer, notification_types):
    Notification.objects.filter(transfer=transfer, notification_type__in=notification_types).delete()


def _log_action(transfer, actor, action, note=''):
    TransferAuditLog.objects.create(
        transfer=transfer,
        actor=actor,
        action=action,
        note=note or '',
    )


def _get_current_assignment_transfer(item, exclude_transfer_id=None):
    queryset = Transfer.objects.filter(
        item=item,
        status__in=[Transfer.STATUS_RECEIVED, Transfer.STATUS_RETURN_REQUESTED],
    )
    if exclude_transfer_id is not None:
        queryset = queryset.exclude(pk=exclude_transfer_id)
    return queryset.order_by('-transfer_date', '-id').first()


def _close_previous_assignment(previous_transfer, actor, note):
    if not previous_transfer:
        return

    previous_transfer.status = Transfer.STATUS_RETURNED
    previous_transfer.returned_date = timezone.now()
    previous_transfer.return_confirmed_by = actor if actor else previous_transfer.return_confirmed_by
    previous_transfer.return_note = note
    previous_transfer.save(update_fields=['status', 'returned_date', 'return_confirmed_by', 'return_note'])

    _clear_notifications(
        previous_transfer,
        [
            Notification.TYPE_TRANSFER_REQUEST,
            Notification.TYPE_TRANSFER_APPROVED,
            Notification.TYPE_RETURN_REQUEST,
            Notification.TYPE_OVERDUE,
        ],
    )
    _log_action(previous_transfer, actor, 'Assignment Closed', note)


def _sync_item_availability(item):
    active_transfers = Transfer.objects.filter(item=item).exclude(
        status__in=[Transfer.STATUS_RETURNED, Transfer.STATUS_CANCELLED, Transfer.STATUS_REJECTED]
    )
    item.assigned_quantity = active_transfers.filter(
        status__in=[Transfer.STATUS_APPROVED, Transfer.STATUS_RECEIVED, Transfer.STATUS_RETURN_REQUESTED]
    ).count()

    if active_transfers.filter(status=Transfer.STATUS_RETURN_REQUESTED).exists():
        item.availability = Item.AVAILABILITY_RETURN_PENDING
    elif active_transfers.filter(status__in=[Transfer.STATUS_APPROVED, Transfer.STATUS_RECEIVED]).exists():
        item.availability = Item.AVAILABILITY_ASSIGNED
    elif active_transfers.filter(status=Transfer.STATUS_AWAITING_APPROVAL).exists():
        item.availability = Item.AVAILABILITY_IN_APPROVAL
    else:
        item.availability = Item.AVAILABILITY_AVAILABLE

    if not item.qr_value:
        item.qr_value = item.item_code
    item.save(update_fields=['assigned_quantity', 'availability', 'qr_value'])


def _sync_overdue_notifications():
    overdue_transfers = Transfer.objects.select_related('item', 'receiver').filter(
        expected_date__lt=timezone.localdate()
    ).exclude(status__in=[
        Transfer.STATUS_RETURNED,
        Transfer.STATUS_CANCELLED,
        Transfer.STATUS_REJECTED,
    ])

    active_overdue_ids = set()
    for transfer in overdue_transfers:
        active_overdue_ids.add(transfer.id)
        users = list(_admin_users()) + [transfer.receiver]
        message = f"{transfer.item.name} should have been returned by {transfer.expected_date} but is still pending."
        _create_notifications(users, transfer, Notification.TYPE_OVERDUE, message)

    Notification.objects.filter(notification_type=Notification.TYPE_OVERDUE).exclude(
        Q(transfer_id__in=active_overdue_ids)
    ).delete()


class CreateTransferView(generics.CreateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not actor:
            return Response({"message": "Please login before submitting a transfer."}, status=400)

        data = request.data

        item = None
        item_id = data.get('item_id')
        if item_id:
            item = Item.objects.filter(pk=item_id).first()

        if not item:
            item = Item.objects.create(
                name=data.get('item_name') or "Unknown",
                category=data.get('category') or 'OTH',
                total_quantity=max(int(data.get('total_quantity') or 1), 1),
                location_note=data.get('location_note') or '',
            )
            if not item.qr_value:
                item.qr_value = item.item_code
                item.save(update_fields=['qr_value'])

        receiver_id = data.get('receiver_id')
        receiver = Employee.objects.filter(pk=receiver_id).first() if receiver_id else None
        if receiver is None:
            return Response(
                {"message": "Select a registered employee as the receiver before submitting the transfer."},
                status=400
            )

        active_assignment = _get_current_assignment_transfer(item) if item else None
        sender = actor
        from_office_id = data.get('from_office') or actor.office_id
        from_floor = data.get('from_floor') or ''
        to_office_id = data.get('to_office') or receiver.office_id
        to_floor = data.get('to_floor') or ''

        if active_assignment and active_assignment.receiver_id == receiver.id:
            return Response({"message": "This item is already assigned to the selected employee."}, status=400)

        if active_assignment and active_assignment.receiver_id != receiver.id:
            current_holder = active_assignment.receiver
            sender = current_holder
            from_office_id = data.get('from_office') or active_assignment.to_office_id
            from_floor = data.get('from_floor') or active_assignment.to_floor

            if not (_is_admin(actor) or actor.id == current_holder.id or actor.id == receiver.id):
                return Response(
                    {"message": "Only the current holder, the receiving employee, or an admin can request this handoff."},
                    status=403,
                )

        transfer = Transfer.objects.create(
            item=item,
            serial_number=data.get('serial_number'),
            description=data.get('description'),
            from_office_id=from_office_id,
            to_office_id=to_office_id,
            from_floor=from_floor,
            to_floor=to_floor,
            sender=sender,
            receiver=receiver,
            probable_days=data.get('probable_days'),
            expected_date=data.get('expected_date'),
            status=Transfer.STATUS_AWAITING_APPROVAL,
            admin_comment=data.get('admin_comment') or '',
        )

        for img in request.FILES.getlist('images'):
            TransferImage.objects.create(transfer=transfer, image=img)

        admins = list(_admin_users())
        if admins:
            if sender.id != actor.id:
                message = f"{actor.name} requested approval to hand over {transfer.item.name} from {sender.name} to {receiver.name}."
            else:
                message = f"{actor.name} requested approval to transfer {transfer.item.name} to {receiver.name}."
            _create_notifications(admins, transfer, Notification.TYPE_TRANSFER_REQUEST, message)

        _log_action(transfer, actor, 'Transfer Requested', transfer.description)
        _sync_item_availability(item)
        _sync_overdue_notifications()
        return Response({"message": "Transfer request submitted for admin approval."}, status=status.HTTP_201_CREATED)


class RequestReturnView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not actor:
            return Response({"message": "Please login before requesting a return."}, status=400)

        obj = self.get_object()
        if actor.id != obj.receiver_id and not _is_admin(actor):
            return Response({"message": "Only the employee who received the item can request a return."}, status=403)
        if obj.status != Transfer.STATUS_RECEIVED:
            return Response({"message": "Return can only be requested after the item is received."}, status=400)

        obj.status = Transfer.STATUS_RETURN_REQUESTED
        obj.return_requested_at = timezone.now()
        obj.return_requested_by = actor
        obj.return_condition = request.data.get('return_condition') or Transfer.CONDITION_GOOD
        obj.return_note = request.data.get('return_note') or ''
        obj.save()

        for img in request.FILES.getlist('return_images'):
            ReturnImage.objects.create(transfer=obj, image=img)

        admins = list(_admin_users())
        if admins:
            message = f"{actor.name} marked {obj.item.name} as returned and is waiting for admin confirmation."
            _create_notifications(admins, obj, Notification.TYPE_RETURN_REQUEST, message)

        _log_action(obj, actor, 'Return Requested', obj.return_note or obj.get_return_condition_display())
        _sync_item_availability(obj.item)
        _sync_overdue_notifications()
        return Response({"message": "Return request submitted for admin confirmation."})


class TransferListView(generics.ListAPIView):
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        actor = _get_actor(self.request)
        if not actor:
            return Transfer.objects.none()

        queryset = Transfer.objects.select_related(
            'item', 'sender', 'receiver', 'from_office', 'to_office', 'approved_by', 'return_confirmed_by', 'rejected_by'
        ).prefetch_related('images', 'return_images', 'audit_logs__actor').order_by('-transfer_date')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        office_filter = self.request.query_params.get('office')
        if office_filter:
            queryset = queryset.filter(Q(from_office_id=office_filter) | Q(to_office_id=office_filter))

        search = (self.request.query_params.get('search') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(item__name__icontains=search)
                | Q(item__item_code__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(sender__name__icontains=search)
                | Q(receiver__name__icontains=search)
            )

        overdue_only = self.request.query_params.get('overdue')
        if overdue_only == '1':
            queryset = queryset.filter(expected_date__lt=timezone.localdate()).exclude(
                status__in=[Transfer.STATUS_RETURNED, Transfer.STATUS_CANCELLED, Transfer.STATUS_REJECTED]
            )

        return queryset


class CancelTransferView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not actor:
            return Response({"message": "Login required."}, status=403)

        obj = self.get_object()
        if obj.status != Transfer.STATUS_AWAITING_APPROVAL:
            return Response({"message": "Only pending transfer requests can be removed."}, status=400)
        if actor.id != obj.sender_id and not _is_admin(actor):
            return Response({"message": "Only the sender or an admin can remove this pending request."}, status=403)

        obj.status = Transfer.STATUS_CANCELLED
        obj.save()

        _clear_notifications(
            obj,
            [Notification.TYPE_TRANSFER_REQUEST, Notification.TYPE_TRANSFER_APPROVED, Notification.TYPE_OVERDUE],
        )
        _log_action(obj, actor, 'Transfer Cancelled', request.data.get('note') or '')
        _sync_item_availability(obj.item)
        _sync_overdue_notifications()
        return Response({"message": "Pending request removed."})


class RejectTransferView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not _is_admin(actor):
            return Response({"message": "Only an admin can reject a transfer."}, status=403)

        obj = self.get_object()
        if obj.status != Transfer.STATUS_AWAITING_APPROVAL:
            return Response({"message": "Only pending transfer requests can be rejected."}, status=400)

        obj.status = Transfer.STATUS_REJECTED
        obj.rejected_by = actor
        obj.rejected_at = timezone.now()
        obj.rejection_reason = request.data.get('rejection_reason') or ''
        obj.save()

        _clear_notifications(obj, [Notification.TYPE_TRANSFER_REQUEST])
        _log_action(obj, actor, 'Transfer Rejected', obj.rejection_reason)
        _sync_item_availability(obj.item)
        return Response({"message": "Transfer rejected."})


class ApproveTransferView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not _is_admin(actor):
            return Response({"message": "Only an admin can approve a transfer."}, status=403)

        obj = self.get_object()
        if obj.status != Transfer.STATUS_AWAITING_APPROVAL:
            return Response({"message": "This transfer is not waiting for admin approval."}, status=400)

        obj.status = Transfer.STATUS_APPROVED
        obj.approved_by = actor
        obj.approved_at = timezone.now()
        obj.admin_comment = request.data.get('admin_comment') or obj.admin_comment
        obj.save()

        previous_assignment = _get_current_assignment_transfer(obj.item, exclude_transfer_id=obj.id)
        if previous_assignment and previous_assignment.receiver_id == obj.sender_id:
            _close_previous_assignment(
                previous_assignment,
                actor,
                f"Assignment moved from {obj.sender.name} to {obj.receiver.name} without an intermediate return.",
            )

        _clear_notifications(obj, [Notification.TYPE_TRANSFER_REQUEST])
        _create_notifications(
            [obj.receiver],
            obj,
            Notification.TYPE_TRANSFER_APPROVED,
            f"{actor.name} approved the transfer of {obj.item.name}. Confirm once the item reaches you.",
        )
        _log_action(obj, actor, 'Transfer Approved', obj.admin_comment)
        _sync_item_availability(obj.item)
        _sync_overdue_notifications()
        return Response({"message": "Transfer approved."})


class ConfirmDeliveryView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not actor:
            return Response({"message": "Please login before confirming delivery."}, status=400)

        obj = self.get_object()
        if actor.id != obj.receiver_id and not _is_admin(actor):
            return Response({"message": "Only the receiver can confirm delivery."}, status=403)
        if obj.status != Transfer.STATUS_APPROVED:
            return Response({"message": "Delivery can only be confirmed after admin approval."}, status=400)

        obj.status = Transfer.STATUS_RECEIVED
        obj.received_date = timezone.now()
        obj.save()

        _clear_notifications(obj, [Notification.TYPE_TRANSFER_APPROVED])
        _log_action(obj, actor, 'Delivery Confirmed', '')
        _sync_item_availability(obj.item)
        _sync_overdue_notifications()
        return Response({"message": "Delivery confirmed."})


class ConfirmReturnView(generics.UpdateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        actor = _get_actor(request)
        if not _is_admin(actor):
            return Response({"message": "Only an admin can confirm the returned item."}, status=403)

        obj = self.get_object()
        if obj.status != Transfer.STATUS_RETURN_REQUESTED:
            return Response({"message": "This item is not waiting for return confirmation."}, status=400)

        obj.status = Transfer.STATUS_RETURNED
        obj.returned_date = timezone.now()
        obj.return_confirmed_by = actor
        obj.admin_comment = request.data.get('admin_comment') or obj.admin_comment
        if request.data.get('return_condition'):
            obj.return_condition = request.data.get('return_condition')
        if request.data.get('return_note'):
            obj.return_note = request.data.get('return_note')
        obj.save()

        _clear_notifications(
            obj,
            [Notification.TYPE_RETURN_REQUEST, Notification.TYPE_OVERDUE, Notification.TYPE_TRANSFER_APPROVED],
        )
        _log_action(obj, actor, 'Return Confirmed', obj.return_note or obj.get_return_condition_display())
        _sync_item_availability(obj.item)
        _sync_overdue_notifications()
        return Response({"message": "Return confirmed."})


@api_view(['GET'])
def dashboard_summary(request):
    actor = _get_actor(request)
    if not actor:
        return Response({})

    transfers = Transfer.objects.select_related('item', 'from_office', 'to_office', 'sender', 'receiver')
    active_transfers = transfers.exclude(
        status__in=[Transfer.STATUS_RETURNED, Transfer.STATUS_CANCELLED, Transfer.STATUS_REJECTED]
    )

    items = Item.objects.all()
    offices = Office.objects.order_by('name')
    overdue_count = transfers.filter(expected_date__lt=timezone.localdate()).exclude(
        status__in=[Transfer.STATUS_RETURNED, Transfer.STATUS_CANCELLED, Transfer.STATUS_REJECTED]
    ).count()

    status_counts = {
        key: transfers.filter(status=key).count()
        for key, _ in Transfer.STATUS_CHOICES
    }

    office_summary = []
    for office in offices:
        office_summary.append({
            'id': office.id,
            'name': office.name,
            'location': office.location,
            'outgoing_transfers': active_transfers.filter(from_office=office).count(),
            'incoming_transfers': active_transfers.filter(to_office=office).count(),
        })

    stock_summary = {
        'total_items': items.count(),
        'available_items': items.filter(availability=Item.AVAILABILITY_AVAILABLE).count(),
        'assigned_items': items.filter(availability=Item.AVAILABILITY_ASSIGNED).count(),
        'approval_items': items.filter(availability=Item.AVAILABILITY_IN_APPROVAL).count(),
        'return_pending_items': items.filter(availability=Item.AVAILABILITY_RETURN_PENDING).count(),
    }

    recent_transfers = TransferSerializer(
        transfers.order_by('-transfer_date')[:6],
        many=True,
        context={'request': request},
    ).data

    return Response({
        'status_counts': status_counts,
        'overdue_count': overdue_count,
        'stock_summary': stock_summary,
        'office_summary': office_summary,
        'recent_transfers': recent_transfers,
    })


@api_view(['GET'])
def export_transfers_csv(request):
    actor = _get_actor(request)
    if not actor:
        return Response({'message': 'Login required.'}, status=403)

    transfers = Transfer.objects.select_related(
        'item', 'sender', 'receiver', 'from_office', 'to_office', 'approved_by', 'return_confirmed_by'
    ).order_by('-transfer_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_transfers.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Item', 'Item Code', 'Serial Number', 'Status', 'Status Meaning', 'Sender', 'Receiver',
        'From Office', 'From Floor', 'To Office', 'To Floor', 'Expected Return', 'Approved By', 'Returned By Admin',
        'Return Condition', 'Admin Comment', 'Rejection Reason'
    ])

    for transfer in transfers:
        writer.writerow([
            transfer.item.name,
            transfer.item.item_code,
            transfer.serial_number,
            transfer.get_status_display(),
            TransferSerializer(instance=transfer).data.get('status_description', ''),
            transfer.sender.name,
            transfer.receiver.name,
            transfer.from_office.name,
            transfer.from_floor,
            transfer.to_office.name,
            transfer.to_floor,
            transfer.expected_date,
            transfer.approved_by.name if transfer.approved_by else '',
            transfer.return_confirmed_by.name if transfer.return_confirmed_by else '',
            transfer.get_return_condition_display(),
            transfer.admin_comment,
            transfer.rejection_reason,
        ])

    return response
