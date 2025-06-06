# Generated by Django 5.2 on 2025-05-03 04:56

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('incentives', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncentiveSetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('title', models.CharField(max_length=255)),
                ('financial_year', models.CharField(max_length=20)),
                ('new_market_eligibility_months', models.PositiveIntegerField(blank=True, null=True)),
                ('new_market_deal_incentive', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('deal_owner', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('lead_source', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('follow_up', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('demo_1', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('demo_2', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('enable_minimum_benchmark', models.BooleanField(default=True)),
                ('enable_75_90_achievement', models.BooleanField(default=True)),
                ('enable_90_95_achievement', models.BooleanField(default=True)),
                ('enable_95_100_achievement', models.BooleanField(default=True)),
                ('enable_above_100_achievement', models.BooleanField(default=True)),
                ('min_subscription_month', models.PositiveIntegerField(blank=True, null=True)),
                ('subscription_100_per_target', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('subscription_75_per_target', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('subscription_50_per_target', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LeadSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('module', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('is_selectable', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Segment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('model_name', models.CharField(max_length=255)),
                ('object_id', models.CharField(max_length=100)),
                ('change_type', models.CharField(max_length=50)),
                ('changed_data', models.JSONField(default=dict)),
                ('new_data', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HighValueDealSlab',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deal_type_high', models.CharField(choices=[('domestic', 'Domestic'), ('international', 'International')], default=1, max_length=20)),
                ('min_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('max_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('incentive_percentage', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('incentive_setup', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='high_value_slabs', to='incentives.incentivesetup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SetupChargeSlab',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deal_type_setup', models.CharField(choices=[('domestic', 'Domestic'), ('international', 'International')], default=1, max_length=20)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('incentive_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('incentive_setup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setup_slabs', to='incentives.incentivesetup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TopperMonthSlab',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deal_type_top', models.CharField(choices=[('domestic', 'Domestic'), ('international', 'International')], default=1, max_length=20)),
                ('min_subscription', models.DecimalField(decimal_places=2, max_digits=10)),
                ('incentive_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('incentive_setup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topper_slabs', to='incentives.incentivesetup')),
                ('segment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='incentives.segment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fullname', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=15)),
                ('mail_id', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=100)),
                ('doj', models.DateField(verbose_name='Date of Joining')),
                ('employee_id', models.CharField(max_length=50, unique=True)),
                ('enable_login', models.BooleanField(default=True)),
                ('user_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='incentives.role')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clientName', models.CharField(max_length=255)),
                ('dealType', models.CharField(choices=[('domestic', 'Domestic'), ('international', 'International')], default='domestic', max_length=15)),
                ('dealWonDate', models.DateField()),
                ('setupCharges', models.DecimalField(decimal_places=2, max_digits=10)),
                ('monthlySubscription', models.DecimalField(decimal_places=2, max_digits=10)),
                ('newMarketPenetration', models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], max_length=3)),
                ('newMarketCountry', models.CharField(blank=True, max_length=255, null=True)),
                ('leadSource', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals', to='incentives.leadsource')),
                ('segment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deal_segment', to='incentives.segment')),
                ('dealownerSalesPerson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_owner', to='incentives.userprofile')),
                ('demo1SalesPerson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_demo1', to='incentives.userprofile')),
                ('demo2SalesPerson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_demo2', to='incentives.userprofile')),
                ('followUpSalesPerson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_followup', to='incentives.userprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnnualTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('financial_year', models.CharField(max_length=10)),
                ('net_salary', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('annual_target_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incentives.userprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('can_add', models.BooleanField(default=False)),
                ('can_edit', models.BooleanField(default=False)),
                ('can_delete', models.BooleanField(default=False)),
                ('can_view', models.BooleanField(default=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incentives.module')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incentives.role')),
            ],
            options={
                'unique_together': {('role', 'module')},
            },
        ),
    ]
