# Generated by Django 5.2 on 2025-05-03 10:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incentives', '0005_alter_deal_leadsource_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deal_id', models.CharField(max_length=255)),
                ('version', models.IntegerField(default=1)),
                ('transaction_type', models.CharField(choices=[('Earned', 'Earned'), ('To Recover', 'To Recover')], max_length=50)),
                ('incentive_component_type', models.CharField(choices=[('setup', 'setup'), ('new_market', 'new_market'), ('topper_month', 'topper_month'), ('single_high', 'single_high')], max_length=100)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('freeze', models.BooleanField(default=False)),
                ('is_latest', models.BooleanField(default=True)),
                ('eligibility_status', models.CharField(choices=[('Pending', 'Pending'), ('Eligible', 'Eligible'), ('Not Eligible', 'Not Eligible')], default='Pending', max_length=50)),
                ('eligibility_message', models.CharField(blank=True, max_length=50, null=True)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_by', models.CharField(max_length=255)),
                ('updated_by', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-transaction_date'],
            },
        ),
        migrations.CreateModel(
            name='PayoutTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deal_id', models.CharField(max_length=255)),
                ('incentive_person_type', models.CharField(choices=[('deal_source', 'Deal Source'), ('deal_owner', 'Deal Owner'), ('follow_up', 'Follow Up'), ('demo_1', 'Demo 1'), ('demo_2', 'Demo 2')], max_length=100)),
                ('payout_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payout_status', models.CharField(choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Hold', 'Hold'), ('Rejected', 'Rejected')], default='Pending', max_length=50)),
                ('payout_message', models.CharField(blank=True, max_length=50, null=True)),
                ('payout_date', models.DateTimeField(auto_now_add=True)),
                ('payment_method', models.CharField(choices=[('Bank Transfer', 'Bank Transfer'), ('Cheque', 'Cheque')], default='Bank Transfer', max_length=100)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('version', models.IntegerField(default=1)),
                ('is_latest', models.BooleanField(default=True)),
                ('created_by', models.CharField(max_length=255)),
                ('updated_by', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('incentive_transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incentives.transaction')),
            ],
            options={
                'verbose_name': 'Payout Transaction',
                'verbose_name_plural': 'Payout Transactions',
                'ordering': ['-payout_date'],
            },
        ),
    ]
