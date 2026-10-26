import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FirmMaster, LedgerMaster

_thread_locals = threading.local()


def is_syncing():
    return getattr(_thread_locals, 'is_syncing', False)


class SyncGuard:
    def __enter__(self):
        _thread_locals.is_syncing = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        _thread_locals.is_syncing = False


@receiver(post_save, sender=FirmMaster)
def sync_firm_to_ledger(sender, instance, created, **kwargs):
    """
    When a Firm Master is created:
    Also creates a corresponding record in Ledger Master with:
    - Ledgercode = FirmCode
    - LEDGERNAME = Firmname
    - group = None (user chooses on edit)
    - address fields blank

    When updated:
    Syncs the ledger name with Firmname.
    """
    if is_syncing():
        return

    with SyncGuard():
        ledger = LedgerMaster.objects.filter(ledger_code=instance.firm_code).first()
        if not ledger:
            LedgerMaster.objects.create(
                ledger_code=instance.firm_code,
                ledger_name=instance.firm_name,
                firm=instance,
                is_firm_ledger=True,
                group=None,
                add1='',
                add2='',
                add3='',
            )
        else:
            updates = {}
            if ledger.ledger_name != instance.firm_name:
                updates['ledger_name'] = instance.firm_name
            if ledger.firm_id != instance.firm_code:
                updates['firm'] = instance
            if not ledger.is_firm_ledger:
                updates['is_firm_ledger'] = True
            if updates:
                LedgerMaster.objects.filter(ledger_code=instance.firm_code).update(**updates)


@receiver(post_save, sender=LedgerMaster)
def sync_ledger_to_firm(sender, instance, created, **kwargs):
    """
    When a Ledger Master is created:
    Also creates a corresponding record in Firm Master with:
    - FirmCode = Ledgercode
    - Firmname = LEDGERNAME
    """
    if is_syncing():
        return

    with SyncGuard():
        firm = FirmMaster.objects.filter(firm_code=instance.ledger_code).first()
        if not firm:
            firm = FirmMaster.objects.create(
                firm_code=instance.ledger_code,
                firm_name=instance.ledger_name
            )
            # Link ledger to the created firm
            LedgerMaster.objects.filter(ledger_code=instance.ledger_code).update(
                firm=firm,
                is_firm_ledger=True
            )
        else:
            if firm.firm_name != instance.ledger_name:
                FirmMaster.objects.filter(firm_code=instance.ledger_code).update(
                    firm_name=instance.ledger_name
                )
            if not instance.is_firm_ledger or instance.firm_id != firm.firm_code:
                LedgerMaster.objects.filter(ledger_code=instance.ledger_code).update(
                    firm=firm,
                    is_firm_ledger=True
                )


@receiver(post_delete, sender=FirmMaster)
def delete_firm_sync_ledger(sender, instance, **kwargs):
    """
    When a Firm Master is deleted, remove the corresponding Ledger.
    """
    if is_syncing():
        return

    with SyncGuard():
        LedgerMaster.objects.filter(ledger_code=instance.firm_code).delete()


@receiver(post_delete, sender=LedgerMaster)
def delete_ledger_sync_firm(sender, instance, **kwargs):
    """
    When a Ledger Master is deleted, remove the corresponding Firm Master.
    """
    if is_syncing():
        return

    with SyncGuard():
        FirmMaster.objects.filter(firm_code=instance.ledger_code).delete()
