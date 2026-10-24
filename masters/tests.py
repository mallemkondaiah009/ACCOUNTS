from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import FirmMaster, GroupMaster, LedgerMaster, GroupCategory


class MasterAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Firm
        self.firm = FirmMaster.objects.create(
            firm_code="HOTEL",
            firm_name="PLATINUM"
        )

        # Create Group
        self.group = GroupMaster.objects.create(
            grp_name="Cash",
            category=GroupCategory.ASSETS
        )

        # Create Ledger
        self.ledger = LedgerMaster.objects.create(
            ledger_code="CASH",
            ledger_name="CASH",
            group=self.group,
            firm=self.firm,
            add1="Counter 1",
            add2="",
            add3=""
        )

    def test_firm_master_crud(self):
        # List
        response = self.client.get(reverse('firm-master-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['FirmCode'], 'HOTEL')

        # Create
        create_payload = {"FirmCode": "GAR", "Firmname": "GARDEN"}
        response = self.client.post(reverse('firm-master-list'), data=create_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(FirmMaster.objects.filter(firm_code="GAR").exists())

    def test_group_master_crud(self):
        # List
        response = self.client.get(reverse('group-master-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['category'], 'ASSETS')

        # Create new group with auto number
        create_payload = {
            "GrpName": "General Exp",
            "category": "EXPENSES"
        }
        response = self.client.post(reverse('group-master-list'), data=create_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('GrpCode', response.data)
        self.assertEqual(response.data['category'], 'EXPENSES')

        # Filter by category
        filter_res = self.client.get(reverse('group-master-list') + '?category=EXPENSES')
        self.assertEqual(len(filter_res.data['results']), 1)
        self.assertEqual(filter_res.data['results'][0]['GrpName'], 'General Exp')

    def test_ledger_master_crud(self):
        # List
        response = self.client.get(reverse('ledger-master-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['Ledgercode'], 'CASH')
        self.assertEqual(response.data['results'][0]['Grpcode'], self.group.grp_code)

        # Create
        create_payload = {
            "Ledgercode": "HDFC",
            "LEDGERNAME": "HDFCBANK",
            "Grpcode": self.group.grp_code,
            "FirmCode": self.firm.firm_code,
            "Add1": "Main Branch",
            "Add2": "MG Road",
            "Add3": ""
        }
        response = self.client.post(reverse('ledger-master-list'), data=create_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Ledgercode'], 'HDFC')

        # Search filter
        search_res = self.client.get(reverse('ledger-master-list') + '?search=HDFC')
        self.assertEqual(len(search_res.data['results']), 1)

    def test_detail_apiviews(self):
        # Firm Detail
        firm_detail = self.client.get(reverse('firm-master-detail', kwargs={'pk': self.firm.firm_code}))
        self.assertEqual(firm_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(firm_detail.data['Firmname'], 'PLATINUM')

        # Group Detail
        grp_detail = self.client.get(reverse('group-master-detail', kwargs={'pk': self.group.grp_code}))
        self.assertEqual(grp_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(grp_detail.data['GrpName'], 'Cash')

        # Ledger Detail
        ledger_detail = self.client.get(reverse('ledger-master-detail', kwargs={'pk': self.ledger.ledger_code}))
        self.assertEqual(ledger_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(ledger_detail.data['LEDGERNAME'], 'CASH')

        # Categories APIView
        cat_res = self.client.get(reverse('group-categories'))
        self.assertEqual(cat_res.status_code, status.HTTP_200_OK)
        self.assertIn('ASSETS', cat_res.data)

        # Delete Ledger
        del_res = self.client.delete(reverse('ledger-master-detail', kwargs={'pk': self.ledger.ledger_code}))
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LedgerMaster.objects.filter(ledger_code="CASH").exists())

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Accounting Master Hub')


