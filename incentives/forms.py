# forms.py
from django import forms
from .models import UserProfile, Deal, AnnualTarget, YearlyIncentive,MonthlyIncentive, SetupChargeSlab, TopperMonthSlab, HighValueDealSlab
from django.forms import inlineformset_factory

class UserProfileForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'id': 'password'}),  # Add ID for JS toggle
        required=False,
        label="Password"
    )

    class Meta:
        model = UserProfile
        fields = ['employee_id', 'fullname', 'username', 'mail_id', 'phone', 'user_type', 'doj', 'password']
        widgets = {
            'doj': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        is_edit = kwargs.pop('is_edit', False)  # If it's editing an existing user
        super().__init__(*args, **kwargs)

        # Set all fields except 'doj' and 'password' as required
        for name in self.fields:
            if name not in ['doj', 'password']:
                self.fields[name].required = True

        self.fields['doj'].required = False  # Make DOJ optional

        # Set password required only during create (not edit)
        if not is_edit:
            self.fields['password'].required = True  # Make password required for new users
            
class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['clientName', 'segment', 'dealType', 'dealWonDate', 'setupCharges', 'monthlySubscription',
                  'newMarketPenetration', 'newMarketCountry', 'dealownerSalesPerson', 'followUpSalesPerson', 
                  'demo1SalesPerson', 'demo2SalesPerson']
        widgets = {
            'dealWonDate': forms.DateInput(attrs={'type': 'date'}),
            'newMarketCountry': forms.TextInput(attrs={'placeholder': 'Enter country name'}),
            'setupCharges': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'monthlySubscription': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'dealownerSalesPerson': forms.Select(attrs={'class': 'form-control'}),
            'followUpSalesPerson': forms.Select(attrs={'class': 'form-control'}),
            'demo1SalesPerson': forms.Select(attrs={'class': 'form-control'}),
            'demo2SalesPerson': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set all fields as optional
        for field in self.fields:
            self.fields[field].required = False
        self.fields['clientName'].required = True
        self.fields['segment'].required = True

        # Conditionally require newMarketCountry
        new_market = self.data.get('newMarketPenetration') or getattr(self.instance, 'newMarketPenetration', None)
        if new_market == 'Yes':
            self.fields['newMarketCountry'].required = True

        # Filter salesperson users for dropdowns
        salespeople = UserProfile.objects.filter(user_type__iexact='salesperson')

        self.fields['dealownerSalesPerson'].queryset = salespeople
        self.fields['followUpSalesPerson'].queryset = salespeople
        self.fields['demo1SalesPerson'].queryset = salespeople
        self.fields['demo2SalesPerson'].queryset = salespeople

class AnnualTargetForm(forms.ModelForm):
    class Meta:
        model = AnnualTarget
        fields = ['employee', 'financial_year', 'annual_target_amount']
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter only salespersons
        self.fields['employee'].queryset = UserProfile.objects.filter(user_type='salesperson')
        self.fields['employee'].label = "Employee Name"
        self.fields['employee'].widget.attrs.update({'class': 'form-control', 'required': 'true'})

        # Financial year from 1993 to 2220
        year_choices = [('', '-- Select Year --')] + [(str(year), str(year)) for year in range(1993, 2221)]
        self.fields['financial_year'].widget = forms.Select(choices=year_choices, attrs={'class': 'form-control', 'required': 'true'})

        self.fields['annual_target_amount'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter amount in Rs.',
            'min': '0',
            'step': '0.01',
        })

class YearlyIncentiveForm(forms.ModelForm):
    class Meta:
        model = YearlyIncentive
        fields = [
            'enable_75_90_achievement',
            'enable_90_95_achievement',
            'enable_95_100_achievement',
            'enable_above100_achievement',
            'enable_8month_achievement',
            'enable_6month_achievement',
            'enable_4month_achievement',
            'enable_0month_achievement',
            'enable_topper_1',
            'enable_topper_2',
            'enable_leader_1',
        ]
        widgets = {
            field: forms.CheckboxInput(attrs={'class': 'form-check-input'})
            for field in fields
        }

class MonthlyIncentiveForm(forms.ModelForm):
    class Meta:
        model = MonthlyIncentive
        fields = '__all__'

SetupSlabFormSet = inlineformset_factory(
    MonthlyIncentive, SetupChargeSlab,
    fields=('min_amount', 'max_amount', 'incentive_percent'),
    extra=1, can_delete=True
)

TopperSlabFormSet = inlineformset_factory(
    MonthlyIncentive, TopperMonthSlab,
    fields=('segment', 'min_subscription', 'incentive_percent'),
    extra=1, can_delete=True
)

HighValueSlabFormSet = inlineformset_factory(
    MonthlyIncentive, HighValueDealSlab,
    fields=('min_value', 'max_value', 'incentive_percent'),
    extra=1, can_delete=True
)