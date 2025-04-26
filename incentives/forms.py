from django import forms
from django.forms import ModelForm
from .models import UserProfile, Deal, AnnualTarget, AnnualTargetIncentive, MonthlyIncentive, SetupChargeRule, HighValueDealSlab, TopperMonthRule, Role, LeadSource, Segment


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['fullname', 'phone', 'mail_id', 'password', 'user_type', 'doj', 'employee_id', 'enable_login']
        widgets = {
            'doj': forms.DateInput(attrs={'type': 'date'}),
            'password': forms.PasswordInput(),
        }

    def clean_mail_id(self):
        email = self.cleaned_data.get('mail_id')
        if UserProfile.objects.filter(mail_id=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class DealForm(ModelForm):
    class Meta:
        model = Deal
        fields = ['clientName', 'segment', 'leadSource', 'dealType', 'dealWonDate', 'setupCharges', 'monthlySubscription', 'newMarketPenetration', 'newMarketCountry', 'dealownerSalesPerson', 'followUpSalesPerson', 'demo1SalesPerson', 'demo2SalesPerson']
        widgets = {
            'dealWonDate': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_clientName(self):
        client_name = self.cleaned_data.get('clientName')
        if Deal.objects.filter(clientName=client_name).exists():
            raise forms.ValidationError("This deal already exists.")
        return client_name


class AnnualTargetForm(ModelForm):
    class Meta:
        model = AnnualTarget
        fields = ['employee', 'net_salary','financial_year', 'annual_target_amount']
        widgets = {
            'annual_target_amount': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_annual_target_amount(self):
        amount = self.cleaned_data.get('annual_target_amount')
        if amount < 0:
            raise forms.ValidationError("Annual target amount must be positive.")
        return amount


class YearlyIncentiveForm(ModelForm):
    class Meta:
        model = AnnualTargetIncentive
        fields = ['financial_year', 'enable_75_90_achievement', 'enable_90_95_achievement', 'enable_95_100_achievement', 'enable_above100_achievement', 'enable_8month_achievement', 'enable_6month_achievement', 'enable_4month_achievement', 'enable_0month_achievement', 'enable_topper_1', 'enable_topper_2', 'enable_leader_1']


class MonthlyIncentiveForm(ModelForm):
    class Meta:
        model = MonthlyIncentive
        fields = ['name', 'deal_type', 'financial_year', 'new_market_incentive_fixed', 'lead_source', 'deal_owner', 'follow_up', 'demo_1', 'demo_2']
        widgets = {
            'new_market_incentive_fixed': forms.NumberInput(attrs={'min': 0}),
            'lead_source': forms.NumberInput(attrs={'min': 0}),
            'deal_owner': forms.NumberInput(attrs={'min': 0}),
            'follow_up': forms.NumberInput(attrs={'min': 0}),
            'demo_1': forms.NumberInput(attrs={'min': 0}),
            'demo_2': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if MonthlyIncentive.objects.filter(name=name).exists():
            raise forms.ValidationError("This incentive rule already exists.")
        return name


class SetupChargeRuleForm(ModelForm):
    class Meta:
        model = SetupChargeRule
        fields = ['rule_set', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'min_amount': forms.NumberInput(attrs={'min': 0}),
            'max_amount': forms.NumberInput(attrs={'min': 0}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError("Incentive percentage must be between 0 and 100.")
        return percentage


class HighValueDealSlabForm(ModelForm):
    class Meta:
        model = HighValueDealSlab
        fields = ['rule_set', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'min_amount': forms.NumberInput(attrs={'min': 0}),
            'max_amount': forms.NumberInput(attrs={'min': 0}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError("Incentive percentage must be between 0 and 100.")
        return percentage


class TopperMonthRuleForm(ModelForm):
    class Meta:
        model = TopperMonthRule
        fields = ['rule_set', 'segment', 'min_subscription', 'incentive_percentage']
        widgets = {
            'min_subscription': forms.NumberInput(attrs={'min': 0}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError("Incentive percentage must be between 0 and 100.")
        return percentage


class RoleForm(ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'is_selectable']


class LeadSourceForm(ModelForm):
    class Meta:
        model = LeadSource
        fields = ['name']


class SegmentForm(ModelForm):
    class Meta:
        model = Segment
        fields = ['name']
