from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from Apps.accounts.models import Employee
from Apps.items.models import Item
from Apps.offices.models import Office

from .models import Transfer


class TransferVisibilityAndHandoffTests(APITestCase):
    def setUp(self):
        self.nasan = Office.objects.create(name='Nasan Office', location='Pune')
        self.aasan = Office.objects.create(name='Aasan Office', location='Pune')
        self.katraj = Office.objects.create(name='Katraj Office', location='Pune')

        self.admin = Employee.objects.create(
            name='Admin User',
            username='admin',
            password='secret',
            phone='1111111111',
            office=self.nasan,
            role=Employee.ROLE_ADMIN,
        )
        self.employee_one = Employee.objects.create(
            name='Employee One',
            username='emp1',
            password='secret',
            phone='2222222222',
            office=self.nasan,
            role=Employee.ROLE_EMPLOYEE,
        )
        self.employee_two = Employee.objects.create(
            name='Employee Two',
            username='emp2',
            password='secret',
            phone='3333333333',
            office=self.aasan,
            role=Employee.ROLE_EMPLOYEE,
        )
        self.viewer = Employee.objects.create(
            name='Viewer User',
            username='viewer',
            password='secret',
            phone='4444444444',
            office=self.katraj,
            role=Employee.ROLE_EMPLOYEE,
        )
        self.item = Item.objects.create(name='Monitor', category='DEV', total_quantity=1)

    def _headers(self, user):
        return {'HTTP_X_EMPLOYEE_ID': str(user.id)}

    def test_regular_employee_can_view_all_transfers(self):
        transfer = Transfer.objects.create(
            item=self.item,
            serial_number='SER-100',
            description='Initial assignment',
            from_office=self.nasan,
            to_office=self.aasan,
            from_floor='1st Floor',
            to_floor='10th Floor',
            sender=self.admin,
            receiver=self.employee_one,
            probable_days=5,
            expected_date=timezone.localdate() + timedelta(days=5),
            status=Transfer.STATUS_RECEIVED,
        )

        response = self.client.get('/api/transfers/list/', **self._headers(self.viewer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], transfer.id)

    def test_receiver_can_request_handoff_without_intermediate_return(self):
        current_transfer = Transfer.objects.create(
            item=self.item,
            serial_number='SER-200',
            description='Assigned to employee one',
            from_office=self.nasan,
            to_office=self.nasan,
            from_floor='1st Floor',
            to_floor='2nd Floor',
            sender=self.admin,
            receiver=self.employee_one,
            probable_days=7,
            expected_date=timezone.localdate() + timedelta(days=7),
            status=Transfer.STATUS_RECEIVED,
        )

        response = self.client.post(
            '/api/transfers/create/',
            {
                'item_id': self.item.id,
                'serial_number': 'SER-200',
                'description': 'Please pass this item to me',
                'from_office': self.nasan.id,
                'from_floor': '2nd Floor',
                'to_office': self.aasan.id,
                'to_floor': '10th Floor',
                'receiver_id': self.employee_two.id,
                'probable_days': 3,
                'expected_date': str(timezone.localdate() + timedelta(days=3)),
            },
            format='json',
            **self._headers(self.employee_two),
        )

        self.assertEqual(response.status_code, 201)
        handoff = Transfer.objects.exclude(pk=current_transfer.id).get()
        self.assertEqual(handoff.sender_id, self.employee_one.id)
        self.assertEqual(handoff.receiver_id, self.employee_two.id)
        self.assertEqual(handoff.status, Transfer.STATUS_AWAITING_APPROVAL)

    def test_transfer_allows_same_sender_and_receiver(self):
        response = self.client.post(
            '/api/transfers/create/',
            {
                'item_id': self.item.id,
                'serial_number': 'SER-201',
                'description': 'Keep assignment with same employee',
                'from_office': self.nasan.id,
                'from_floor': '1st Floor',
                'to_office': self.nasan.id,
                'to_floor': '1st Floor',
                'receiver_id': self.employee_one.id,
                'probable_days': 2,
                'expected_date': str(timezone.localdate() + timedelta(days=2)),
            },
            format='json',
            **self._headers(self.employee_one),
        )

        self.assertEqual(response.status_code, 201)
        transfer = Transfer.objects.get(serial_number='SER-201')
        self.assertEqual(transfer.sender_id, self.employee_one.id)
        self.assertEqual(transfer.receiver_id, self.employee_one.id)
        self.assertEqual(transfer.status, Transfer.STATUS_AWAITING_APPROVAL)

    def test_approving_handoff_closes_previous_assignment(self):
        current_transfer = Transfer.objects.create(
            item=self.item,
            serial_number='SER-300',
            description='Assigned to employee one',
            from_office=self.nasan,
            to_office=self.nasan,
            from_floor='1st Floor',
            to_floor='2nd Floor',
            sender=self.admin,
            receiver=self.employee_one,
            probable_days=7,
            expected_date=timezone.localdate() + timedelta(days=7),
            status=Transfer.STATUS_RECEIVED,
        )
        next_transfer = Transfer.objects.create(
            item=self.item,
            serial_number='SER-300',
            description='Move to employee two',
            from_office=self.nasan,
            to_office=self.aasan,
            from_floor='2nd Floor',
            to_floor='10th Floor',
            sender=self.employee_one,
            receiver=self.employee_two,
            probable_days=4,
            expected_date=timezone.localdate() + timedelta(days=4),
            status=Transfer.STATUS_AWAITING_APPROVAL,
        )

        response = self.client.put(
            f'/api/transfers/approve/{next_transfer.id}/',
            {'admin_comment': 'Approved handoff'},
            format='json',
            **self._headers(self.admin),
        )

        self.assertEqual(response.status_code, 200)
        current_transfer.refresh_from_db()
        next_transfer.refresh_from_db()
        self.assertEqual(next_transfer.status, Transfer.STATUS_APPROVED)
        self.assertEqual(current_transfer.status, Transfer.STATUS_RETURNED)
        self.assertIn('Assignment moved', current_transfer.return_note)


class OfficeFloorDefaultsTests(TestCase):
    def test_default_floors_match_known_offices(self):
        nasan = Office.objects.create(name='Nasan Office', location='Pune')
        aasan = Office.objects.create(name='Aasan Office', location='Pune')
        katraj = Office.objects.create(name='Katraj Office', location='Pune')

        self.assertEqual(nasan.get_floor_options(), ['1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor'])
        self.assertEqual(aasan.get_floor_options(), ['10th Floor', '11th Floor'])
        self.assertEqual(katraj.get_floor_options(), [])
