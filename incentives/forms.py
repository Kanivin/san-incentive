from django import forms
from django.forms import ModelForm
from decimal import Decimal
from django import forms
from .models import UserProfile, Deal, Role, LeadSource, Segment, Module, AnnualTarget, IncentiveSetup, SetupChargeSlab, TopperMonthSlab, HighValueDealSlab


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
            'clientName', 'segment', 'leadSource', 'dealType', 'dealWonDate', 'subDate', 'subrenewDate',
            'subAmount', 'setupCharges', 'monthlySubscription', 'newMarketPenetration', 'newMarketCountry',
            'dealownerSalesPerson', 'followUpSalesPerson', 'demo1SalesPerson', 'demo2SalesPerson',
            'refDocs', 'status',
        ]
        widgets = {
            'dealWonDate': forms.DateInput(attrs={'type': 'date'}),
            'subDate': forms.DateInput(attrs={'type': 'date'}),
            'subrenewDate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter user profiles
        user_types = ['salesperson', 'saleshead']
        salesperson_queryset = UserProfile.objects.filter(user_type__name__in=user_types)
        self.fields['dealownerSalesPerson'].queryset = salesperson_queryset
        self.fields['followUpSalesPerson'].queryset = salesperson_queryset
        self.fields['demo1SalesPerson'].queryset = salesperson_queryset
        self.fields['demo2SalesPerson'].queryset = salesperson_queryset

        lead_types = ['salesperson', 'saleshead', 'admin']
        self.fields['leadSource'].queryset = UserProfile.objects.filter(user_type__name__in=lead_types)

        # Optional fields
        self.fields['newMarketPenetration'].required = False
        self.fields['newMarketCountry'].required = False
        self.fields['status'].required = False
        self.fields['refDocs'].required = False

    def clean_clientName(self):
        client_name = self.cleaned_data.get('clientName')
        if client_name and Deal.objects.filter(clientName=client_name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A deal with this client name already exists.")
        return client_name

    def clean(self):
        cleaned_data = super().clean()
        deal_type = cleaned_data.get('dealType')
        new_market_penetration = cleaned_data.get('newMarketPenetration')
        new_market_country = cleaned_data.get('newMarketCountry')

        if deal_type and deal_type.lower() == 'international':
            if not new_market_penetration:
                self.add_error('newMarketPenetration', 'This field is required for International deals.')

            if new_market_penetration and new_market_penetration.lower() == 'yes' and not new_market_country:
                self.add_error('newMarketCountry', 'Please specify the new market country.')

        return cleaned_data
       
class AnnualTargetForm(forms.ModelForm):
    class Meta:
        model = AnnualTarget
        fields = ['employee', 'financial_year', 'net_salary', 'annual_target_amount']
        widgets = {
            'annual_target_amount': forms.NumberInput(attrs={'min': 0}),
            'net_salary': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])
   
        self.fields['employee'].empty_label = "Select Employee"
        self.fields['financial_year'].empty_label = "-- Select Year --"

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



class IncentiveSetupForm(forms.ModelForm):
    class Meta:
        model = IncentiveSetup
        fields = [
            'financial_year', 
            'lead_source',
            'new_market_eligibility_months', 'new_market_deal_incentive', 
            'deal_owner', 'follow_up', 'demo_1', 'demo_2',
            'enable_minimum_benchmark', 'enable_75_90_achievement', 'enable_90_95_achievement',
            'enable_95_100_achievement', 'enable_above_100_achievement',
            'min_subscription_month', 'subscription_100_per_target',
            'subscription_75_per_target', 'subscription_50_per_target',
            'subscription_below_50_per', 'enable_topper_1', 'enable_topper_2', 'enable_leader_1'
        ]
        widgets = {
            'financial_year': forms.TextInput(attrs={'class': 'form-control'}),
            'new_market_eligibility_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'new_market_deal_incentive': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deal_owner': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lead_source': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'follow_up': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'demo_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'demo_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'enable_minimum_benchmark': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_75_90_achievement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_90_95_achievement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_95_100_achievement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_above_100_achievement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_subscription_month': forms.NumberInput(attrs={'class': 'form-control'}),
            'subscription_100_per_target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subscription_75_per_target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subscription_50_per_target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subscription_below_50_per': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'enable_topper_1': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_topper_2': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_leader_1': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields optional except 'financial_year'
        for field_name in self.fields:
            if field_name != 'financial_year':
                self.fields[field_name].required = False


class SetupChargeSlabForm(forms.ModelForm):
    class Meta:
        model = SetupChargeSlab
        fields = ['incentive_setup', 'deal_type_setup', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'incentive_setup': forms.Select(attrs={'class': 'form-control'}),
            'deal_type_setup': forms.Select(attrs={'class': 'form-control'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'incentive_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class TopperMonthSlabForm(forms.ModelForm):
    class Meta:
        model = TopperMonthSlab
        fields = ['incentive_setup','deal_type_top', 'segment', 'min_subscription', 'incentive_percentage']
        widgets = {
            'incentive_setup': forms.Select(attrs={'class': 'form-control'}),
                        'deal_type_top': forms.Select(attrs={'class': 'form-control'}),

            'segment': forms.Select(attrs={'class': 'form-control'}),
            'min_subscription': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'incentive_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class HighValueDealSlabForm(forms.ModelForm):
    class Meta:
        model = HighValueDealSlab
        fields = ['incentive_setup', 'deal_type_high', 'min_amount', 'max_amount', 'incentive_percentage']
        widgets = {
            'incentive_setup': forms.Select(attrs={'class': 'form-control'}),
                        'deal_type_high': forms.Select(attrs={'class': 'form-control'}),

            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'incentive_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
