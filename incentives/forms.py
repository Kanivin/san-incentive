from django import forms
from django.forms import ModelForm
from decimal import Decimal

from .models import (
    UserProfile, Deal, AnnualTarget, AnnualTargetIncentive, MonthlyIncentive,
    SetupChargeRule, HighValueDealSlab, TopperMonthRule, Role, LeadSource, Segment, Module
)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def clean_mail_id(self):
        mail_id = self.cleaned_data.get('mail_id')
        if not mail_id:
            raise forms.ValidationError("Email is required.")

        qs = UserProfile.objects.filter(mail_id__iexact=mail_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This email is already in use.")
        return mail_id


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'clientName', 'segment', 'leadSource', 'dealType', 'dealWonDate',
            'setupCharges', 'monthlySubscription', 'newMarketPenetration', 'newMarketCountry',
            'dealownerSalesPerson', 'followUpSalesPerson', 'demo1SalesPerson', 'demo2SalesPerson'
        ]
        widgets = {
            'dealWonDate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter user profiles for salesperson and saleshead only
        user_types = ['salesperson', 'saleshead']
        salesperson_queryset = UserProfile.objects.filter(user_type__name__in=user_types)
        self.fields['dealownerSalesPerson'].queryset = salesperson_queryset
        self.fields['followUpSalesPerson'].queryset = salesperson_queryset
        self.fields['demo1SalesPerson'].queryset = salesperson_queryset
        self.fields['demo2SalesPerson'].queryset = salesperson_queryset

        # Important: Initially make 'newMarketPenetration' not required
        self.fields['newMarketPenetration'].required = False
        self.fields['newMarketCountry'].required = False

    def clean_clientName(self):
        client_name = self.cleaned_data.get('clientName')
        if Deal.objects.filter(clientName=client_name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("A deal with this client name already exists.")
        return client_name

    def clean(self):
        cleaned_data = super().clean()
        deal_type = cleaned_data.get('dealType')
        new_market_penetration = cleaned_data.get('newMarketPenetration')
        new_market_country = cleaned_data.get('newMarketCountry')

        # Only if dealType is 'international', then newMarketPenetration is required
        if deal_type and deal_type.lower() == 'international':
            if not new_market_penetration:
                self.add_error('newMarketPenetration', 'This field is required for International deals.')

            # If "newMarketPenetration" is "Yes", then newMarketCountry must also be filled
            if new_market_penetration == 'yes' and not new_market_country:
                self.add_error('newMarketCountry', 'Please specify the new market country.')

        return cleaned_data
       
class AnnualTargetForm(forms.ModelForm):
    class Meta:
        model = AnnualTarget
        fields = ['employee', 'financial_year', 'net_salary', 'annual_target_amount']
        widgets = {
            'annual_target_amount': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adjust the employee queryset for selecting only specific user types
        self.fields['employee'].queryset = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])

    def clean_annual_target_amount(self):
        annual_target_amount = self.cleaned_data['annual_target_amount']
        if isinstance(annual_target_amount, Decimal):
            return float(annual_target_amount)  # Convert Decimal to float
        return annual_target_amount

    def clean_net_salary(self):
        net_salary = self.cleaned_data['net_salary']
        if isinstance(net_salary, Decimal):
            return float(net_salary)  # Convert Decimal to float
        return net_salary

    def clean_annual_target_amount(self):
        amount = self.cleaned_data.get('annual_target_amount')
        if amount < 0:
            raise forms.ValidationError("Annual target amount must be positive.")
        return amount


class YearlyIncentiveForm(ModelForm):
    class Meta:
        model = AnnualTargetIncentive
        fields = [
            'financial_year',
            'enable_75_90_achievement', 'enable_90_95_achievement', 'enable_95_100_achievement', 'enable_above100_achievement',
            'enable_8month_achievement', 'enable_6month_achievement', 'enable_4month_achievement', 'enable_0month_achievement',
            'enable_topper_1', 'enable_topper_2', 'enable_leader_1'
        ]


class MonthlyIncentiveForm(ModelForm):
    class Meta:
        model = MonthlyIncentive
        fields = [
            'name', 'deal_type', 'financial_year',
            'new_market_incentive_fixed',  'deal_owner',
            'follow_up', 'demo_1', 'demo_2'
        ]
        widgets = {
            'new_market_incentive_fixed': forms.NumberInput(attrs={'min': 0}),
            'lead_source': forms.NumberInput(attrs={'min': 0}),
            'deal_owner': forms.NumberInput(attrs={'min': 0}),
            'follow_up': forms.NumberInput(attrs={'min': 0}),
            'demo_1': forms.NumberInput(attrs={'min': 0}),
            'demo_2': forms.NumberInput(attrs={'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if name and MonthlyIncentive.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This incentive rule already exists.")
        return cleaned_data

from django import forms
from django.forms import ModelForm
from .models import SetupChargeRule, HighValueDealSlab, TopperMonthRule

class SetupChargeRuleForm(ModelForm):
    class Meta:
        model = SetupChargeRule
        fields = ['rule_set', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'min_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage is None:
            raise forms.ValidationError("This field is required.")
        if not (0 <= percentage <= 100):
            raise forms.ValidationError("Incentive percentage must be between 0 and 100.")
        return percentage


class HighValueDealSlabForm(ModelForm):
    class Meta:
        model = HighValueDealSlab
        fields = ['rule_set', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'min_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage is None:
            raise forms.ValidationError("This field is required.")
        if not (0 <= percentage <= 100):
            raise forms.ValidationError("Incentive percentage must be between 0 and 100.")
        return percentage


class TopperMonthRuleForm(ModelForm):
    class Meta:
        model = TopperMonthRule
        fields = ['rule_set', 'segment', 'min_subscription', 'incentive_percentage']
        widgets = {
            'min_subscription': forms.NumberInput(attrs={'min': 0, 'step': '1'}),
            'incentive_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
        }

    def clean_incentive_percentage(self):
        percentage = self.cleaned_data.get('incentive_percentage')
        if percentage is None:
            raise forms.ValidationError("This field is required.")
        if not (0 <= percentage <= 100):
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

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['module'] 