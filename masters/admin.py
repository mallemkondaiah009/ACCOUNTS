from django.contrib import admin
from .models import FirmMaster, GroupMaster, LedgerMaster, Transaction


@admin.register(FirmMaster)
class FirmMasterAdmin(admin.ModelAdmin):
    list_display = ('firm_code', 'firm_name', 'created_at', 'updated_at')
    search_fields = ('firm_code', 'firm_name')
    ordering = ('firm_code',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GroupMaster)
class GroupMasterAdmin(admin.ModelAdmin):
    list_display = ('grp_code', 'grp_name', 'category', 'super_group', 'created_at')
    list_filter = ('category',)
    search_fields = ('grp_name', 'grp_code')
    ordering = ('grp_code',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LedgerMaster)
class LedgerMasterAdmin(admin.ModelAdmin):
    list_display = ('ledger_code', 'ledger_name', 'group', 'get_category', 'add1', 'add2', 'add3', 'created_at')
    list_filter = ('group__category', 'group')
    search_fields = ('ledger_code', 'ledger_name', 'add1', 'add2', 'add3')
    ordering = ('ledger_code',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Category', ordering='group__category')
    def get_category(self, obj):
        return obj.group.category if obj.group else '-'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'vch_number',
        'vch_type',
        'vch_date',
        'firm',
        'ledger_code',
        'ref_code',
        'type',
        'contra',
        'amount',
        'remarks'
    )
    list_filter = ('vch_type', 'firm', 'type', 'contra', 'vch_date')
    search_fields = (
        'vch_number',
        'ledger_code',
        'ref_code',
        'remarks',
        'firm__firm_code',
        'firm__firm_name'
    )
    ordering = ('-vch_date', 'firm', '-vch_number', 'contra')
    date_hierarchy = 'vch_date'
    readonly_fields = ('created_at', 'updated_at')
