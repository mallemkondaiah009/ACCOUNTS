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
        null=True,
        blank=True,
        help_text="5 numeric Foreign Key to Group Master GrpCode"
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


class VoucherType(models.TextChoices):
    CASH_RECEIPT = 'CR', 'Cash Receipt'
    BANK_RECEIPT = 'BR', 'Bank Receipt'
    CASH_PAYMENT = 'CP', 'Cash Payment'
    BANK_PAYMENT = 'BP', 'Bank Payment'
    JOURNAL_VOUCHER = 'JV', 'Journal Voucher'


class TransactionType(models.TextChoices):
    CREDIT = 'C', 'Credit'
    DEBIT = 'D', 'Debit'


class Transaction(models.Model):
    """
    Transaction Table (trans) as specified in new software.xlsx:
    - vch_type: char(5) (CR, BR, CP, BP)
    - vch_number: numeric / int
    - vch_date: date
    - firm: FK to FirmMaster (FIRMCODE)
    - ledger_code: char(5)
    - ref_code: char(5)
    - remarks: char(50)
    - chq_no: char(10) (optional/nullable)
    - amount: float / decimal
    - type: char(1) ('C' for Credit, 'D' for Debit)
    - contra: int (0 for Primary entry, 1 for Contra balancing entry)
    """
    firm = models.ForeignKey(
        FirmMaster,
        on_delete=models.PROTECT,
        related_name='transactions',
        db_column='firm_code',
        help_text="Firm code reference"
    )
    vch_type = models.CharField(
        max_length=5,
        choices=VoucherType.choices,
        default=VoucherType.CASH_RECEIPT,
        db_column='vch_type'
    )
    vch_number = models.IntegerField(db_column='vch_number')
    vch_date = models.DateField(db_column='vch_date')
    ledger = models.ForeignKey(
        LedgerMaster,
        on_delete=models.PROTECT,
        related_name='transactions',
        db_column='Ledger_code',
        help_text="Primary ledger account reference"
    )
    ref_code = models.CharField(max_length=5, db_column='ref_code')
    remarks = models.CharField(max_length=50, blank=True, default='', db_column='remarks')
    chq_no = models.CharField(max_length=10, blank=True, null=True, db_column='Chq No')
    amount = models.DecimalField(max_digits=12, decimal_places=2, db_column='amount')
    type = models.CharField(
        max_length=1,
        choices=TransactionType.choices,
        db_column='type'
    )
    contra = models.IntegerField(
        choices=[(0, 'Primary'), (1, 'Contra')],
        default=0,
        db_column='CONTRA'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        if 'ledger_code' in kwargs and 'ledger_id' not in kwargs and 'ledger' not in kwargs:
            kwargs['ledger_id'] = kwargs.pop('ledger_code')
        super().__init__(*args, **kwargs)

    @property
    def ledger_code(self):
        return self.ledger_id

    @ledger_code.setter
    def ledger_code(self, value):
        self.ledger_id = value

    class Meta:
        db_table = 'trans'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-vch_date', '-vch_number', 'contra']
        constraints = [
            models.UniqueConstraint(
                fields=['firm', 'vch_type', 'vch_number', 'contra'],
                name='unique_voucher_entry_line'
            )
        ]

    def __str__(self):
        return f"{self.firm_id} | {self.vch_type}-{self.vch_number} | {self.type} {self.amount} ({self.ledger_code})"
