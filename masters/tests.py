from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import FirmMaster, GroupMaster, LedgerMaster, GroupCategory


class MasterAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Group
        self.group = GroupMaster.objects.create(
            grp_name="Cash",
            category=GroupCategory.ASSETS
        )

        # Create Firm (signal will auto-create ledger 'HOTEL')
        self.firm = FirmMaster.objects.create(
            firm_code="HOTEL",
            firm_name="PLATINUM"
        )

        # Create Regular Ledger
        self.ledger = LedgerMaster.objects.create(
            ledger_code="CASH",
            ledger_name="CASH",
            group=self.group,
            add1="Counter 1",
            add2="",
            add3="",
            is_firm_ledger=False
        )

    def test_firm_master_crud_and_auto_ledger_sync(self):
        # List firms
        response = self.client.get(reverse('firm-master-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['FirmCode'], 'HOTEL')

        # Auto-created ledger for HOTEL must exist and be marked as firm ledger
        hotel_ledger = LedgerMaster.objects.filter(ledger_code="HOTEL").first()
        self.assertIsNotNone(hotel_ledger)
        self.assertEqual(hotel_ledger.ledger_name, "PLATINUM")
        self.assertTrue(hotel_ledger.is_firm_ledger)

        # Create new firm GAR -> GARDEN
        create_payload = {"FirmCode": "GAR", "Firmname": "GARDEN"}
        response = self.client.post(reverse('firm-master-list'), data=create_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(FirmMaster.objects.filter(firm_code="GAR").exists())

        # Verify GAR was automatically created in Ledger Master
        gar_ledger = LedgerMaster.objects.filter(ledger_code="GAR").first()
        self.assertIsNotNone(gar_ledger)
        self.assertEqual(gar_ledger.ledger_name, "GARDEN")
        self.assertTrue(gar_ledger.is_firm_ledger)

        # Update firm code and name (FirmCode is editable)
        update_res = self.client.put(
            reverse('firm-master-detail', kwargs={'pk': 'GAR'}),
            data={"FirmCode": "GARDN", "Firmname": "GARDEN RESORT"}
        )
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertFalse(FirmMaster.objects.filter(firm_code="GAR").exists())
        self.assertTrue(FirmMaster.objects.filter(firm_code="GARDN").exists())
        self.assertFalse(LedgerMaster.objects.filter(ledger_code="GAR").exists())
        gardn_ledger = LedgerMaster.objects.filter(ledger_code="GARDN").first()
        self.assertIsNotNone(gardn_ledger)
        self.assertEqual(gardn_ledger.ledger_name, "GARDEN RESORT")

        # Delete firm -> should remove auto-created ledger
        del_res = self.client.delete(reverse('firm-master-detail', kwargs={'pk': 'GARDN'}))
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LedgerMaster.objects.filter(ledger_code="GARDN").exists())

    def test_firm_ledger_code_and_name_locked_but_rest_editable(self):
        # HOTEL is an auto firm ledger
        hotel_ledger = LedgerMaster.objects.get(ledger_code="HOTEL")
        self.assertTrue(hotel_ledger.is_firm_ledger)
        self.assertEqual(hotel_ledger.ledger_name, "PLATINUM")

        # Create another group to test switching groups
        new_group = GroupMaster.objects.create(
            grp_name="Debtors",
            category=GroupCategory.ASSETS
        )

        # Updating Grpcode and Address details SUCCEEDS
        edit_payload = {
            "Ledgercode": "HOTEL",
            "LEDGERNAME": "PLATINUM",
            "Grpcode": new_group.grp_code,
            "Add1": "Tower A",
            "Add2": "Floor 5",
            "Add3": "City Center"
        }
        res_put = self.client.put(
            reverse('ledger-master-detail', kwargs={'pk': 'HOTEL'}),
            data=edit_payload
        )
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)
        hotel_ledger.refresh_from_db()
        self.assertEqual(hotel_ledger.group, new_group)
        self.assertEqual(hotel_ledger.add1, "Tower A")
        self.assertEqual(hotel_ledger.add2, "Floor 5")
        self.assertEqual(hotel_ledger.add3, "City Center")
        # Code and name remain locked to the firm
        self.assertEqual(hotel_ledger.ledger_code, "HOTEL")
        self.assertEqual(hotel_ledger.ledger_name, "PLATINUM")

        # Deleting via ledger endpoint deletes both ledger and firm
        res_del = self.client.delete(reverse('ledger-master-detail', kwargs={'pk': 'HOTEL'}))
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LedgerMaster.objects.filter(ledger_code="HOTEL").exists())
        self.assertFalse(FirmMaster.objects.filter(firm_code="HOTEL").exists())


    def test_ledger_creation_auto_creates_firm_master(self):
        # Creating a ledger in Ledger Master also creates it in Firm Master
        create_payload = {
            "Ledgercode": "HDFC",
            "LEDGERNAME": "HDFCBANK",
            "Grpcode": self.group.grp_code,
            "Add1": "Main Branch",
            "Add2": "MG Road",
            "Add3": ""
        }
        response = self.client.post(reverse('ledger-master-list'), data=create_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Ledgercode'], 'HDFC')
        self.assertTrue(response.data['is_firm_ledger'])

        # Verify FirmMaster was auto-created
        hdfc_firm = FirmMaster.objects.filter(firm_code="HDFC").first()
        self.assertIsNotNone(hdfc_firm)
        self.assertEqual(hdfc_firm.firm_name, "HDFCBANK")

        # Deleting ledger also deletes the associated firm
        del_res = self.client.delete(reverse('ledger-master-detail', kwargs={'pk': 'HDFC'}))
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LedgerMaster.objects.filter(ledger_code="HDFC").exists())
        self.assertFalse(FirmMaster.objects.filter(firm_code="HDFC").exists())

    def test_group_master_crud(self):
        # List
        response = self.client.get(reverse('group-master-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Accounting Master Management')
