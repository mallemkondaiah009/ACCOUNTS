from django.contrib import admin
from .models import FirmMaster, GroupMaster, LedgerMaster


@admin.register(FirmMaster)
class FirmMasterAdmin(admin.ModelAdmin):
    list_display = ('firm_code', 'firm_name', 'created_at')
    search_fields = ('firm_code', 'firm_name')
    ordering = ('firm_code',)


@admin.register(GroupMaster)
class GroupMasterAdmin(admin.ModelAdmin):
    list_display = ('grp_code', 'grp_name', 'category', 'super_group', 'created_at')
    list_filter = ('category',)
    search_fields = ('grp_name',)
    ordering = ('grp_code',)


@admin.register(LedgerMaster)
class LedgerMasterAdmin(admin.ModelAdmin):
    list_display = ('ledger_code', 'ledger_name', 'group', 'firm', 'add1', 'add2', 'add3')
    list_filter = ('group__category', 'group', 'firm')
    search_fields = ('ledger_code', 'ledger_name', 'add1', 'add2', 'add3')
    ordering = ('ledger_code',)
