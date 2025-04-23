from django.db import models


class SiteSettings(models.Model):
    theme_color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code for the theme")

    def __str__(self):
        return f"Site Settings (Theme Color: {self.theme_color})"

USER_TYPE_CHOICES = [
    ('admin', 'Admin'),
    ('accounts', 'Accounts'),
    ('salesperson', 'Salesperson'),
]

class UserProfile(models.Model):
    fullname = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # Use hashed passwords in production!
    phone = models.CharField(max_length=15)
    mail_id = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    doj = models.DateField(verbose_name="Date of Joining")
    employee_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.fullname} ({self.user_type})"
    
class Deal(models.Model):
    SEGMENT_CHOICES = [
        ('Pharma', 'Pharma SFA'),
        ('FMCG', 'FMCG'),
        ('Payroll', 'Payroll'),
    ]

    DEAL_TYPE_CHOICES = [
        ('Domestic', 'Domestic'),
        ('International', 'International'),
    ]

    clientName = models.CharField(max_length=255)
    segment = models.CharField(max_length=255, choices=SEGMENT_CHOICES)
    dealType = models.CharField(max_length=255, choices=DEAL_TYPE_CHOICES)
    dealWonDate = models.DateField()
    setupCharges = models.DecimalField(max_digits=10, decimal_places=2)
    monthlySubscription = models.DecimalField(max_digits=10, decimal_places=2)
    newMarketPenetration = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')
    newMarketCountry = models.CharField(max_length=255, blank=True, null=True)
    dealownerSalesPerson = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='owner_deals')
    followUpSalesPerson = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    demo1SalesPerson = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='demo1_deals')
    demo2SalesPerson = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='demo2_deals')

    def __str__(self):
        return self.clientName

class AnnualTarget(models.Model):
    employee = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=10)
    annual_target_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.employee.fullname} - {self.financial_year}"
    
# class YearlyIncentive(models.Model):
#     # Annual Target Achievement
#     enable_75_90_achievement = models.BooleanField(default=True)
#     enable_90_95_achievement = models.BooleanField(default=True)
#     enable_95_100_achievement = models.BooleanField(default=True)
#     enable_above100_achievement = models.BooleanField(default=True)

#     # Subscription Incentive (on collection)
#     enable_8month_achievement = models.BooleanField(default=True)
#     enable_6month_achievement = models.BooleanField(default=True)
#     enable_4month_achievement = models.BooleanField(default=True)
#     enable_0month_achievement = models.BooleanField(default=True)

#     # Best Performer
#     enable_topper_1 = models.BooleanField(default=True)
#     enable_topper_2 = models.BooleanField(default=True)

#     # Best Team Leader
#     enable_leader_1 = models.BooleanField(default=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Yearly Incentive Setup ({self.id})"
    


class RuleSet(models.Model):
    DEAL_TYPES = [('domestic', 'Domestic'), ('international', 'International')]

    name = models.CharField(max_length=255)
    deal_type = models.CharField(max_length=50, choices=DEAL_TYPES)
    financial_year = models.CharField(max_length=50)
    new_market_incentive_fixed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('deal_type', 'financial_year')
        db_table = 'rule_sets'

    def __str__(self):
        return f"{self.name} - {self.deal_type} ({self.financial_year})"


class SetupChargeRule(models.Model):
    rule_set = models.ForeignKey(RuleSet, on_delete=models.CASCADE, related_name='setup_charge_rules')
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'setup_charge_rules'


class DealBifurcationRule(models.Model):
    rule_set = models.OneToOneField(RuleSet, on_delete=models.CASCADE, related_name='deal_bifurcation_rule')
    deal_owner_lead_pct = models.DecimalField(max_digits=5, decimal_places=2)
    follow_up_pct = models.DecimalField(max_digits=5, decimal_places=2)
    demo_1_pct = models.DecimalField(max_digits=5, decimal_places=2)
    demo_2_pct = models.DecimalField(max_digits=5, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deal_bifurcation_rules'


class SpecialAwardsRule(models.Model):
    rule_set = models.OneToOneField(RuleSet, on_delete=models.CASCADE, related_name='special_awards_rule')
    enable_topper_1 = models.BooleanField()
    enable_topper_2 = models.BooleanField()
    enable_team_leader = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'special_awards_rules'


class TopperMonthRule(models.Model):
    rule_set = models.ForeignKey(RuleSet, on_delete=models.CASCADE, related_name='topper_month_rules')
    segment = models.CharField(max_length=100)
    min_subscription = models.DecimalField(max_digits=10, decimal_places=2)
    incentive_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'topper_month_rules'


class AnnualTargetIncentive(models.Model):
    rule_set = models.OneToOneField(RuleSet, on_delete=models.CASCADE, related_name='annual_target_incentive')
    enable_75_90 = models.BooleanField()
    multiplier_75_90 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enable_90_95 = models.BooleanField()
    multiplier_90_95 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enable_95_100 = models.BooleanField()
    multiplier_95_100 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enable_100_plus = models.BooleanField()
    multiplier_100_plus = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'annual_target_incentives'


class SubscriptionIncentive(models.Model):
    rule_set = models.OneToOneField(RuleSet, on_delete=models.CASCADE, related_name='subscription_incentive')
    enable_100_plus_annual = models.BooleanField()
    months_100_plus_annual = models.IntegerField(null=True, blank=True)

    enable_75_99_9_annual = models.BooleanField()
    months_75_99_9_annual = models.IntegerField(null=True, blank=True)

    enable_50_74_9_annual = models.BooleanField()
    months_50_74_9_annual = models.IntegerField(null=True, blank=True)

    enable_less_50_annual = models.BooleanField()
    months_less_50_annual = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_incentives'


