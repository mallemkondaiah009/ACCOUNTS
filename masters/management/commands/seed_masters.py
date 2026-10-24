from django.core.management.base import BaseCommand
from masters.models import FirmMaster, GroupMaster, LedgerMaster, GroupCategory


class Command(BaseCommand):
    help = 'Seeds sample data for Firm Master, Group Master, and Ledger Master from specification sheet'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Firm Master...")
        firms_data = [
            {"firm_code": "HOTEL", "firm_name": "PLATINUM"},
            {"firm_code": "GAR", "firm_name": "GARDEN"},
        ]
        firms = {}
        for f in firms_data:
            obj, created = FirmMaster.objects.update_or_create(
                firm_code=f["firm_code"],
                defaults={"firm_name": f["firm_name"]}
            )
            firms[obj.firm_code] = obj
            self.stdout.write(f"  {'Created' if created else 'Updated'} Firm: {obj}")

        self.stdout.write("Seeding Group Master...")
        groups_data = [
            {"grp_code": 1, "grp_name": "General Exp", "category": GroupCategory.EXPENSES},
            {"grp_code": 2, "grp_name": "Bank interes", "category": GroupCategory.INCOME},
            {"grp_code": 3, "grp_name": "Firm", "category": GroupCategory.LIABILITIES},
            {"grp_code": 4, "grp_name": "Cash", "category": GroupCategory.ASSETS},
            {"grp_code": 5, "grp_name": "BANK", "category": GroupCategory.ASSETS},
            {"grp_code": 6, "grp_name": "DEBTORS", "category": GroupCategory.ASSETS},
        ]
        groups = {}
        for g in groups_data:
            obj, created = GroupMaster.objects.update_or_create(
                grp_code=g["grp_code"],
                defaults={
                    "grp_name": g["grp_name"],
                    "category": g["category"],
                    "super_group": None
                }
            )
            groups[obj.grp_code] = obj
            self.stdout.write(f"  {'Created' if created else 'Updated'} Group: {obj}")

        self.stdout.write("Seeding Ledger Master...")
        ledgers_data = [
            {
                "ledger_code": "HDFC",
                "ledger_name": "HDFCBANK",
                "grp_code": 5,
                "firm_code": "HOTEL",
                "add1": "Main Branch",
                "add2": "MG Road",
                "add3": "City"
            },
            {
                "ledger_code": "CASH",
                "ledger_name": "CASH",
                "grp_code": 4,
                "firm_code": "HOTEL",
                "add1": "Cash Counter 1",
                "add2": "",
                "add3": ""
            },
            {
                "ledger_code": "RAM",
                "ledger_name": "RAM KUMAR",
                "grp_code": 6,
                "firm_code": "GAR",
                "add1": "Suite 101",
                "add2": "Park Street",
                "add3": ""
            },
            {
                "ledger_code": "SRI",
                "ledger_name": "SRI",
                "grp_code": 6,
                "firm_code": "GAR",
                "add1": "Plot 24",
                "add2": "Sector 5",
                "add3": ""
            },
            {
                "ledger_code": "MAL",
                "ledger_name": "MALLEM",
                "grp_code": 6,
                "firm_code": "HOTEL",
                "add1": "Bazaar Street",
                "add2": "",
                "add3": ""
            },
            {
                "ledger_code": "TEA",
                "ledger_name": "TEA",
                "grp_code": 1,
                "firm_code": "HOTEL",
                "add1": "Pantry Expenses",
                "add2": "",
                "add3": ""
            },
            {
                "ledger_code": "INT",
                "ledger_name": "BANK SAVIN",
                "grp_code": 2,
                "firm_code": "HOTEL",
                "add1": "Savings Interest",
                "add2": "",
                "add3": ""
            },
        ]

        for l in ledgers_data:
            obj, created = LedgerMaster.objects.update_or_create(
                ledger_code=l["ledger_code"],
                defaults={
                    "ledger_name": l["ledger_name"],
                    "group": groups[l["grp_code"]],
                    "firm": firms.get(l.get("firm_code")),
                    "add1": l.get("add1", ""),
                    "add2": l.get("add2", ""),
                    "add3": l.get("add3", ""),
                }
            )
            self.stdout.write(f"  {'Created' if created else 'Updated'} Ledger: {obj}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded all master records!"))
