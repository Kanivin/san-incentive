from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


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
    

    leadSource = models.ForeignKey(LeadSource, related_name='deals', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.clientName



class AnnualTarget(AuditMixin):
    employee = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=10)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_target_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.employee.fullname} - {self.financial_year}"


class AnnualTargetIncentive(AuditMixin):
    financial_year = models.CharField(max_length=50)
    reduction_period = models.CharField(max_length=50,null=True)
    enable_75_90_achievement = models.BooleanField(default=True)
    enable_90_95_achievement = models.BooleanField(default=True)
    enable_95_100_achievement = models.BooleanField(default=True)
    enable_above100_achievement = models.BooleanField(default=True)
    enable_8month_achievement = models.BooleanField(default=True)
    enable_6month_achievement = models.BooleanField(default=True)
    enable_4month_achievement = models.BooleanField(default=True)
    enable_0month_achievement = models.BooleanField(default=True)
    enable_topper_1 = models.BooleanField(default=True)
    enable_topper_2 = models.BooleanField(default=True)
    enable_leader_1 = models.BooleanField(default=True)

    def __str__(self):
        return f"Annual Incentive Setup ({self.id})"


class MonthlyIncentive(AuditMixin):
    DEAL_TYPES = [('domestic', 'Domestic'), ('international', 'International')]

    name = models.CharField(max_length=255,blank=True)
    deal_type = models.CharField(max_length=50, choices=DEAL_TYPES)
    financial_year = models.CharField(max_length=50)
    new_market_incentive_fixed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_source = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    deal_owner = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    follow_up = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    demo_1 = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    demo_2 = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)

    class Meta:
        unique_together = ('deal_type', 'financial_year')
        db_table = 'rule_sets'

    def __str__(self):
        return f"{self.name} - {self.deal_type} ({self.financial_year})"


class SetupChargeRule(AuditMixin):
    rule_set = models.ForeignKey(MonthlyIncentive, on_delete=models.CASCADE, related_name='setup_charge_rules', null=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'setup_charge_rules'


class HighValueDealSlab(AuditMixin):
    rule_set = models.ForeignKey(MonthlyIncentive, on_delete=models.CASCADE, related_name='high_value_slabs', null=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'single_value_rules'


class TopperMonthRule(AuditMixin):
    rule_set = models.ForeignKey(MonthlyIncentive, on_delete=models.CASCADE, related_name='topper_month_rules', null=True)
    segment = models.ForeignKey(Segment, related_name='top_segment', on_delete=models.CASCADE, null=True, blank=True)
    min_subscription = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'topper_month_rules'