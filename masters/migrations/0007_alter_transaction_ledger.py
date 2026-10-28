import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0006_alter_transaction_vch_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='ledger_code',
            new_name='ledger',
        ),
        migrations.AlterField(
            model_name='transaction',
            name='ledger',
            field=models.ForeignKey(
                db_column='Ledger_code',
                help_text='Primary ledger account reference',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='transactions',
                to='masters.ledgermaster',
            ),
        ),
    ]
