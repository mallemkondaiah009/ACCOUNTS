import re
from rest_framework import serializers
from .models import FirmMaster, GroupMaster, LedgerMaster, GroupCategory


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
        required=False,
        allow_null=True
    )
    group_name = serializers.CharField(source='group.grp_name', read_only=True, allow_null=True)
    group_category = serializers.CharField(source='group.category', read_only=True, allow_null=True)
    FirmCode = serializers.PrimaryKeyRelatedField(
        source='firm',
        queryset=FirmMaster.objects.all(),
        required=False,
        allow_null=True
    )
    firm_name = serializers.CharField(source='firm.firm_name', read_only=True)
    is_firm_ledger = serializers.BooleanField(read_only=True)
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
            'FirmCode',
            'firm_name',
            'is_firm_ledger',
            'Add1',
            'Add2',
            'Add3',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_firm_ledger', 'created_at', 'updated_at']

    def validate_Ledgercode(self, value):
        validate_alphanumeric(value, 'Ledgercode')
        return value.strip()

    def validate_LEDGERNAME(self, value):
        validate_alphanumeric(value, 'LEDGERNAME')
        return value.strip()

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if instance and instance.is_firm_ledger:
            new_name = attrs.get('ledger_name')
            if new_name and new_name.strip() != instance.ledger_name:
                raise serializers.ValidationError({
                    'LEDGERNAME': 'Ledger name for a Firm ledger is managed by Firm Master and cannot be edited in Ledger Master.'
                })
        return attrs

