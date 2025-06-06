# Generated by Django 5.2 on 2025-05-26 04:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incentives', '0012_deal_refdocs_deal_subamount_deal_subdate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='team_head',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salespersons', to='incentives.userprofile', verbose_name='Reports To'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='incentives.role', verbose_name='Role'),
        ),
    ]
