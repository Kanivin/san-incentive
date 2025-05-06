from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

class AuditMixin(models.Model):
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(AuditMixin):
    name = models.CharField(max_length=50, unique=True)
    is_selectable = models.BooleanField(default=True)  # Hide 'superadmin' from UI

    def __str__(self):
        return self.name


class Module(AuditMixin):
    module = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.module


class Permission(AuditMixin):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_view = models.BooleanField(default=True)

    class Meta:
        unique_together = ('role', 'module')


class UserProfile(AuditMixin):
    fullname = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    mail_id = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    user_type = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True)
    doj = models.DateField(verbose_name="Date of Joining")
    employee_id = models.CharField(max_length=50, unique=True)
    enable_login = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fullname} ({self.user_type})"
    


class ChangeLog(AuditMixin):
    model_name = models.CharField(max_length=255)
    object_id = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_id')
    change_type = models.CharField(max_length=50)
    changed_data = models.JSONField(default=dict)
    new_data = models.JSONField(default=dict, blank=True, null=True)  # <-- Add this line
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.content_type_id and self.content_object:
            self.content_type = ContentType.objects.get_for_model(self.content_object.__class__)
        super().save(*args, **kwargs)



class Segment(AuditMixin):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class LeadSource(AuditMixin):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Deal(AuditMixin):
    DOMESTIC = 'domestic'
    INTERNATIONAL = 'international'

    DEAL_TYPE_CHOICES = [
        (DOMESTIC, 'Domestic'),
        (INTERNATIONAL, 'International'),
    ]
    
    clientName = models.CharField(max_length=255)
    segment = models.ForeignKey(Segment, related_name='deal_segment', on_delete=models.CASCADE, null=True, blank=True)
    dealType = models.CharField(
        max_length=15,
        choices=DEAL_TYPE_CHOICES,
        default=DOMESTIC,  # or any default you prefer
    )
    dealWonDate = models.DateField()
    setupCharges = models.DecimalField(max_digits=10, decimal_places=2)
    monthlySubscription = models.DecimalField(max_digits=10, decimal_places=2)
    newMarketPenetration = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')])
    newMarketCountry = models.CharField(max_length=255, blank=True, null=True)

    dealownerSalesPerson = models.ForeignKey(UserProfile, related_name='deals_as_owner', on_delete=models.CASCADE, null=True, blank=True)
    followUpSalesPerson = models.ForeignKey(UserProfile, related_name='deals_as_followup', on_delete=models.CASCADE, null=True, blank=True)
    demo1SalesPerson = models.ForeignKey(UserProfile, related_name='deals_as_demo1', on_delete=models.CASCADE, null=True, blank=True)
    demo2SalesPerson = models.ForeignKey(UserProfile, related_name='deals_as_demo2', on_delete=models.CASCADE, null=True, blank=True)
    leadSource = models.ForeignKey(UserProfile, related_name='leadsource', on_delete=models.CASCADE, null=True, blank=True)
 
    status = models.CharField(max_length=255, default="Non Approve")

    def __str__(self):
        return self.clientName



class AnnualTarget(AuditMixin):
    employee = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=10)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_target_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.employee.fullname} - {self.financial_year}"


class IncentiveSetup(AuditMixin):
    title = models.CharField(max_length=255)
    financial_year = models.CharField(max_length=20)
    
    # New Market Penetration
    new_market_eligibility_months = models.PositiveIntegerField(null=True, blank=True)
    new_market_deal_incentive = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Deal Bifurcation
    deal_owner = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lead_source = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    follow_up = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    demo_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    demo_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Annual Target
    enable_minimum_benchmark = models.BooleanField(default=True)
    enable_75_90_achievement = models.BooleanField(default=True)
    enable_90_95_achievement = models.BooleanField(default=True)
    enable_95_100_achievement = models.BooleanField(default=True)
    enable_above_100_achievement = models.BooleanField(default=True)

    # Subscription Incentive
    min_subscription_month = models.PositiveIntegerField(null=True, blank=True)
    subscription_100_per_target = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    subscription_75_per_target = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    subscription_50_per_target = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    subscription_below_50_per = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    enable_topper_1 = models.BooleanField(default=False)
    enable_topper_2 = models.BooleanField(default=False)
    enable_leader_1 = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SetupChargeSlab(AuditMixin):
    incentive_setup = models.ForeignKey(IncentiveSetup, related_name="setup_slabs", on_delete=models.CASCADE)
    deal_type_setup = models.CharField(max_length=20, default='domestic')
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2)


class TopperMonthSlab(AuditMixin):
    incentive_setup = models.ForeignKey(IncentiveSetup, related_name="topper_slabs", on_delete=models.CASCADE)
    deal_type_top = models.CharField(max_length=20, default='domestic')
    segment = models.ForeignKey('Segment', on_delete=models.SET_NULL, null=True)  # assuming a Segment model exists
    min_subscription = models.DecimalField(max_digits=10, decimal_places=2)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2)


class HighValueDealSlab(AuditMixin):
    incentive_setup = models.ForeignKey(IncentiveSetup, related_name="high_value_slabs", on_delete=models.CASCADE,null=True)
    deal_type_high = models.CharField(max_length=20, default='domestic')
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)


class Transaction(AuditMixin):
    DEAL_TYPE_CHOICES = [
        ('Earned', 'Earned'),
        ('To Recover', 'To Recover'),
    ]
    
    ELIGIBILITY_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Eligible', 'Eligible'),
        ('Not Eligible', 'Not Eligible'),
    ]
    
    TRANSACTION_COMPONENT_CHOICES = [
        ('setup', 'Setup'),
        ('new_market', 'New Market'),
        ('topper_month', 'Topper of the Month'),
        ('single_high', 'Single High Value'),
    ]

    deal_id = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    transaction_type = models.CharField(max_length=50, choices=DEAL_TYPE_CHOICES)
    incentive_component_type = models.CharField(max_length=100, choices=TRANSACTION_COMPONENT_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    freeze = models.BooleanField(default=False)
    is_latest = models.BooleanField(default=True)
    
    eligibility_status = models.CharField(max_length=50, choices=ELIGIBILITY_STATUS_CHOICES, default='Pending')
    eligibility_message = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.deal_id} - {self.transaction_type}"

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-transaction_date']

class PayoutTransaction(AuditMixin):
    INCENTIVE_PERSON_CHOICES = [
        ('deal_source', 'Deal Source'),
        ('deal_owner', 'Deal Owner'),
        ('follow_up', 'Follow Up'),
        ('demo_1', 'Demo 1'),
        ('demo_2', 'Demo 2'),
    ]
    
    PAYOUT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Hold', 'Hold'),
        ('Rejected', 'Rejected'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
    ]

    deal_id = models.CharField(max_length=255)
    incentive_transaction = models.ForeignKey(
        'Transaction', 
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    user = models.ForeignKey(UserProfile, related_name='payout_trans', on_delete=models.CASCADE, null=True, blank=True)
    
    incentive_person_type = models.CharField(max_length=100, choices=INCENTIVE_PERSON_CHOICES)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payout_status = models.CharField(max_length=50, choices=PAYOUT_STATUS_CHOICES, default='Pending')
    payout_message = models.CharField(max_length=50, blank=True, null=True)
    payout_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHOD_CHOICES, default='Bank Transfer')
    transaction_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)

    def __str__(self):
        return f"Payout {self.deal_id} - {self.incentive_person_type}"

    class Meta:
        verbose_name = 'Payout Transaction'
        verbose_name_plural = 'Payout Transactions'
        ordering = ['-payout_date']