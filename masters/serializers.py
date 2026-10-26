import re
from decimal import Decimal
from rest_framework import serializers
from .models import (
    FirmMaster,
    GroupMaster,
    LedgerMaster,
    GroupCategory,
    Transaction,
    VoucherType,
    TransactionType
)


def validate_alphanumeric(value, field_name):
    if value and not re.match(r'^[a-zA-Z0-9\s\-_.,/&()]+$', str(value)):
        raise serializers.ValidationError(
            f"{field_name} must contain only alphanumeric characters, spaces, or standard symbols."
        )
    return value


class FirmMasterSerializer(serializers.ModelSerializer):
    # Support both Excel-style naming and snake_case
    FirmCode = serializers.CharField(source='firm_code', max_length=5)
    Firmname = serializers.CharField(source='firm_name', max_length=50)

    class Meta:
        model = FirmMaster
        fields = [
            'FirmCode',
            'Firmname',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_FirmCode(self, value):
        validate_alphanumeric(value, 'FirmCode')
        return value.strip()

    def validate_Firmname(self, value):
        validate_alphanumeric(value, 'Firmname')
        return value.strip()


class GroupMasterSerializer(serializers.ModelSerializer):
    GrpCode = serializers.IntegerField(source='grp_code', read_only=True)
    GrpName = serializers.CharField(source='grp_name', max_length=50)
    Super = serializers.PrimaryKeyRelatedField(
        source='super_group',
        queryset=GroupMaster.objects.all(),
        required=False,
        allow_null=True
    )
    super_name = serializers.CharField(source='super_group.grp_name', read_only=True)
    category = serializers.ChoiceField(choices=GroupCategory.choices)

    class Meta:
        model = GroupMaster
        fields = [
            'GrpCode',
            'GrpName',
            'category',
            'Super',
            'super_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['GrpCode', 'created_at', 'updated_at']

    def validate_GrpName(self, value):
        validate_alphanumeric(value, 'GrpName')
        return value.strip()

    def validate(self, attrs):
        # Prevent self-referencing super group
        instance = getattr(self, 'instance', None)
        super_group = attrs.get('super_group')
        if instance and super_group and instance.grp_code == super_group.grp_code:
            raise serializers.ValidationError({'Super': "A group cannot be its own Super group."})
        return attrs


class LedgerMasterSerializer(serializers.ModelSerializer):
    Ledgercode = serializers.CharField(source='ledger_code', max_length=5)
    LEDGERNAME = serializers.CharField(source='ledger_name', max_length=50)
    Grpcode = serializers.PrimaryKeyRelatedField(
        source='group',
        queryset=GroupMaster.objects.all(),
        required=True,
        allow_null=False,
        error_messages={
            'null': 'Group is required. Please select a group.',
            'required': 'Group is required. Please select a group.'
        }
    )
    group_name = serializers.CharField(source='group.grp_name', read_only=True, allow_null=True)
    group_category = serializers.CharField(source='group.category', read_only=True, allow_null=True)
    Add1 = serializers.CharField(source='add1', max_length=50, required=False, allow_blank=True)
    Add2 = serializers.CharField(source='add2', max_length=50, required=False, allow_blank=True)
    Add3 = serializers.CharField(source='add3', max_length=50, required=False, allow_blank=True)

    class Meta:
        model = LedgerMaster
        fields = [
            'Ledgercode',
            'LEDGERNAME',
            'Grpcode',
            'group_name',
            'group_category',
            'Add1',
            'Add2',
            'Add3',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_Ledgercode(self, value):
        validate_alphanumeric(value, 'Ledgercode')
        return value.strip()

    def validate_LEDGERNAME(self, value):
        validate_alphanumeric(value, 'LEDGERNAME')
        return value.strip()


class TransactionSerializer(serializers.ModelSerializer):
    firm_code = serializers.CharField(source='firm.firm_code', read_only=True)
    firm_name = serializers.CharField(source='firm.firm_name', read_only=True)
    ledger_name = serializers.SerializerMethodField()
    ref_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'firm_code',
            'firm_name',
            'vch_type',
            'vch_number',
            'vch_date',
            'ledger_code',
            'ledger_name',
            'ref_code',
            'ref_name',
            'remarks',
            'chq_no',
            'amount',
            'type',
            'contra',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_ledger_name(self, obj):
        ledger = LedgerMaster.objects.filter(ledger_code=obj.ledger_code).first()
        return ledger.ledger_name if ledger else obj.ledger_code

    def get_ref_name(self, obj):
        ledger = LedgerMaster.objects.filter(ledger_code=obj.ref_code).first()
        return ledger.ledger_name if ledger else obj.ref_code


class CashReceiptCreateSerializer(serializers.Serializer):
    firm_code = serializers.CharField(max_length=5)
    vch_date = serializers.DateField()
    ledger_code = serializers.CharField(max_length=5)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    remarks = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')

    def validate_firm_code(self, value):
        value = value.strip()
        if not FirmMaster.objects.filter(firm_code=value).exists():
            raise serializers.ValidationError("Selected Firm does not exist.")
        return value

    def validate_ledger_code(self, value):
        value = value.strip()
        if value.upper() == 'CASH':
            raise serializers.ValidationError("Party ledger cannot be CASH for a Cash Receipt.")
        if not LedgerMaster.objects.filter(ledger_code=value).exists():
            raise serializers.ValidationError(f"Ledger '{value}' does not exist.")
        return value


