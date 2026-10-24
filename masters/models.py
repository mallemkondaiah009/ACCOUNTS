from django.db import models


class FirmMaster(models.Model):
    """
    Firm Master:
    - FirmCode: 5 alpha numeric (Primary Key)
    - Firmname: 50 alpha numeric
    """
    firm_code = models.CharField(
        max_length=5,
        primary_key=True,
        db_column='FirmCode',
        help_text="5 alphanumeric characters"
    )
    firm_name = models.CharField(
        max_length=50,
        db_column='Firmname',
        help_text="Firm name up to 50 characters"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'firm_master'
        verbose_name = 'Firm Master'
        verbose_name_plural = 'Firm Masters'
        ordering = ['firm_code']

    def __str__(self):
        return f"{self.firm_code} - {self.firm_name}"


class GroupCategory(models.TextChoices):
    INCOME = 'INCOME', 'INCOME'
    EXPENSES = 'EXPENSES', 'EXPENSES'
    ASSETS = 'ASSETS', 'ASSETS'
    LIABILITIES = 'LIABILITIES', 'LIABILITIES'


class GroupMaster(models.Model):
    """
    Group Master:
    - GrpCode: 5 numeric (Auto No - AutoField PK)
    - GrpName: 50 alpha numeric
    - category / Drop Down: INCOME, EXPENSES, ASSETS, LIABILITIES
    - Super: 5 numeric (Super group code / parent group)
    """
    grp_code = models.AutoField(
        primary_key=True,
        db_column='GrpCode',
        help_text="5 numeric Auto No"
    )
    grp_name = models.CharField(
        max_length=50,
        db_column='GrpName',
        help_text="Group name up to 50 characters"
    )
    category = models.CharField(
        max_length=20,
        choices=GroupCategory.choices,
        db_column='Category',
        help_text="Drop Down: INCOME, EXPENSES, ASSETS, LIABILITIES"
    )
    super_group = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_groups',
        db_column='Super',
        help_text="Super group code (5 numeric, parent group reference)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_master'
        verbose_name = 'Group Master'
        verbose_name_plural = 'Group Masters'
        ordering = ['grp_code']

    def __str__(self):
        return f"{self.grp_code} - {self.grp_name} ({self.category})"


class LedgerMaster(models.Model):
    """
    Ledger Master:
    - Ledgercode: 5 alpha numeric
    - LEDGERNAME: 50 alpha numeric
    - Grpcode: 5 numeric (Foreign Key to Group Master)
    - Add1: 50 alpha numeric
    - Add2: 50 alpha numeric
    - Add3: 50 alpha numeric
    - Optional Firm foreign key for multi-company ledger setup
    """
    ledger_code = models.CharField(
        max_length=5,
        primary_key=True,
        db_column='Ledgercode',
        help_text="5 alphanumeric characters"
    )
    ledger_name = models.CharField(
        max_length=50,
        db_column='LEDGERNAME',
        help_text="Ledger name up to 50 characters"
    )
    group = models.ForeignKey(
        GroupMaster,
        on_delete=models.PROTECT,
        related_name='ledgers',
        db_column='Grpcode',
        help_text="5 numeric Foreign Key to Group Master GrpCode"
    )
    firm = models.ForeignKey(
        FirmMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ledgers',
        db_column='FirmCode',
        help_text="Optional Foreign Key to Firm Master"
    )
    add1 = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_column='Add1',
        help_text="Address Line 1 (50 characters)"
    )
    add2 = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_column='Add2',
        help_text="Address Line 2 (50 characters)"
    )
    add3 = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_column='Add3',
        help_text="Address Line 3 (50 characters)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ledger_master'
        verbose_name = 'Ledger Master'
        verbose_name_plural = 'Ledger Masters'
        ordering = ['ledger_code']

    def __str__(self):
        return f"{self.ledger_code} - {self.ledger_name}"
