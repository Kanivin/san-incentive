# Generated by Django 5.2 on 2025-05-29 14:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('incentives', '0017_remove_transaction_deal_id_transaction_deal'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='deal',
            new_name='deal_id',
        ),
    ]
