# Generated by Django 5.2 on 2025-05-29 08:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('incentives', '0014_remove_payouttransaction_deal_id_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TragetTransaction',
            new_name='TargetTransaction',
        ),
    ]
