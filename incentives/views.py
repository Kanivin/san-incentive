from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password

from .models import UserProfile, Deal, AnnualTarget,Segment, LeadSource,AnnualTargetIncentive, MonthlyIncentive, SetupChargeRule, TopperMonthRule, HighValueDealSlab
from .forms import UserProfileForm,LeadSourceForm, SegmentForm,DealForm, AnnualTargetForm, MonthlyIncentiveForm, SetupChargeRuleForm, TopperMonthRuleForm, HighValueDealSlabForm, YearlyIncentiveForm
from django.forms import modelformset_factory

# ---------- Authentication Views ----------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('mail_id')
        password = request.POST.get('password')
        next_url = request.GET.get('next')

        try:
            user = UserProfile.objects.get(mail_id=username)
            if check_password(password, user.password):
                request.session['mail_id'] = user.mail_id
                user_type = user.user_type.lower()

                if user_type == 'superadmin':
                    return redirect(next_url or 'superadmin_dashboard')
                elif user_type == 'accounts':
                    return redirect('accounts_dashboard')
                elif user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('sales_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


# ---------- Dashboard Views ----------

def admin_dashboard(request):
    return render(request, 'owner/dashboard.html')

def accounts_dashboard(request):
    return render(request, 'accounts/dashboard.html')

def superadmin_dashboard(request):
    return render(request, 'super/dashboard.html')

def sales_dashboard(request):
    return render(request, 'sales/dashboard.html')


# ---------- User Management Views ----------

def user_list(request):
    users = UserProfile.objects.all()
    return render(request, 'owner/users/user_list.html', {'users': users})

def user_create(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserProfileForm()
    return render(request, 'owner/users/user_form.html', {'form': form, 'title': 'Create User'})

def user_edit(request, pk):
    user = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'owner/users/user_form.html', {'form': form, 'title': 'Edit User'})

def user_delete(request, pk):
    user = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'owner/users/user_confirm_delete.html', {'user': user})

# Segment Views
def segment_list(request):
    segments = Segment.objects.all()
    return render(request, 'owner/segment/segment_list.html', {'segments': segments})

def segment_create(request):
    if request.method == 'POST':
        form = SegmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('segment_list')
    else:
        form = SegmentForm()
    return render(request, 'owner/segment/segment_form.html', {'form': form, 'title': 'Create Segment'})

def segment_edit(request, pk):
    segment = get_object_or_404(Segment, pk=pk)
    if request.method == 'POST':
        form = SegmentForm(request.POST, instance=segment)
        if form.is_valid():
            form.save()
            return redirect('segment_list')
    else:
        form = SegmentForm(instance=segment)
    return render(request, 'owner/segment/segment_form.html', {'form': form, 'title': 'Edit Segment'})

def segment_delete(request, pk):
    segment = get_object_or_404(Segment, pk=pk)
    if request.method == 'POST':
        segment.delete()
        return redirect('segment_list')
    return render(request, 'owner/segment/segment_confirm_delete.html', {'segment': segment})

# Lead Source Views
def leadsource_list(request):
    lead_sources = LeadSource.objects.all()
    return render(request, 'owner/leadsource/leadsource_list.html', {'lead_sources': lead_sources})

def leadsource_create(request):
    if request.method == 'POST':
        form = LeadSourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leadsource_list')
    else:
        form = LeadSourceForm()
    return render(request, 'owner/leadsource/leadsource_form.html', {'form': form, 'title': 'Create Lead Source'})

def leadsource_edit(request, pk):
    lead_source = get_object_or_404(LeadSource, pk=pk)
    if request.method == 'POST':
        form = LeadSourceForm(request.POST, instance=lead_source)
        if form.is_valid():
            form.save()
            return redirect('leadsource_list')
    else:
        form = LeadSourceForm(instance=lead_source)
    return render(request, 'owner/leadsource/leadsource_form.html', {'form': form, 'title': 'Edit Lead Source'})

def leadsource_delete(request, pk):
    lead_source = get_object_or_404(LeadSource, pk=pk)
    if request.method == 'POST':
        lead_source.delete()
        return redirect('leadsource_list')
    return render(request, 'owner/leadsource/leadsource_confirm_delete.html', {'lead_source': lead_source})

# ---------- Deal Management Views ----------

def deal_list(request):
    deals = Deal.objects.all()
    return render(request, 'owner/deal/deal_list.html', {'deals': deals})

def deal_create(request):
    if request.method == 'POST':
        form = DealForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('deal_list')
    else:
        form = DealForm()
    return render(request, 'owner/deal/deal_form.html', {'form': form, 'action': 'Create', 'title': 'Create Deal'})

def deal_update(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            form.save()
            return redirect('deal_list')
    else:
        form = DealForm(instance=deal)
    return render(request, 'owner/deal/deal_form.html', {'form': form, 'action': 'Update', 'deal': deal, 'title': 'Update Deal'})

def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        deal.delete()
        return redirect('deal_list')
    return render(request, 'owner/deal/deal_confirm_delete.html', {'deal': deal})


# ---------- Annual Target Views ----------

def target_list(request):
    targets = AnnualTarget.objects.all()
    return render(request, 'owner/annual_target/target_list.html', {'targets': targets})

def target_create(request):
    if request.method == 'POST':
        form = AnnualTargetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('target_list')
    else:
        form = AnnualTargetForm()

    employees = UserProfile.objects.filter(user_type='salesperson')
    
    # Generate years like "2024-2025"
    financial_years = [f"{year}-{year+1}" for year in range(1993, 2220)]

    return render(request, 'owner/annual_target/target_form.html', {
        'form': form,
        'employees': employees,
        'financial_years': financial_years,
        'title': 'Create Annual Target',
        'action': 'Create'
    })

def target_update(request, pk):
    target = get_object_or_404(AnnualTarget, pk=pk)
    if request.method == 'POST':
        form = AnnualTargetForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            return redirect('target_list')
    else:
        form = AnnualTargetForm(instance=target)
    return render(request, 'owner/annual_target/target_form.html', {'form': form, 'action': 'Update', 'target': target, 'title': 'Update Annual Target'})

def target_delete(request, pk):
    target = get_object_or_404(AnnualTarget, pk=pk)
    if request.method == 'POST':
        target.delete()
        return redirect('target_list')
    return render(request, 'owner/annual_target/target_confirm_delete.html', {'target': target})


# ---------- Monthly Incentive Views ----------

def monthlyin_create(request):
    if request.method == 'POST':
        form = MonthlyIncentiveForm(request.POST)
        setup_formset = SetupChargeRuleForm(request.POST, prefix='setup')
        topper_formset = TopperMonthRuleForm(request.POST, prefix='topper')
        high_formset = HighValueDealSlabForm(request.POST, prefix='high')

        if form.is_valid() and setup_formset.is_valid() and topper_formset.is_valid() and high_formset.is_valid():
            incentive = form.save()
            setup_formset.instance = incentive
            setup_formset.save()
            topper_formset.instance = incentive
            topper_formset.save()
            high_formset.instance = incentive
            high_formset.save()
            return redirect('monthlyin_list')
    else:
        form = MonthlyIncentiveForm()
        setup_formset = SetupChargeRuleForm(prefix='setup')
        topper_formset = TopperMonthRuleForm(prefix='topper')
        high_formset = HighValueDealSlabForm(prefix='high')

    return render(request, 'owner/monthlyin/monthlyin_form.html', {
        'form': form,
        'setup_formset': setup_formset,
        'topper_formset': topper_formset,
        'high_formset': high_formset,
        'title': 'Create Monthly Incentive'
    })


def monthlyin_update(request, pk):
    incentive = get_object_or_404(MonthlyIncentive, pk=pk)

    SetupSlabFormSet = modelformset_factory(SetupChargeRule, form=SetupSlabFormSet, extra=0, can_delete=True)
    TopperFormSet = modelformset_factory(TopperMonthRule, form=TopperMonthRuleForm, extra=0, can_delete=True)
    HighValueFormSet = modelformset_factory(HighValueDealSlab, form=HighValueDealSlabForm, extra=0, can_delete=True)

    if request.method == 'POST':
        form = MonthlyIncentiveForm(request.POST, instance=incentive)
        setup_formset = SetupSlabFormSet(request.POST, queryset=SetupChargeRule.objects.filter(incentive=incentive), prefix='setup')
        topper_formset = TopperFormSet(request.POST, queryset=TopperMonthRule.objects.filter(incentive=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(request.POST, queryset=HighValueDealSlab.objects.filter(incentive=incentive), prefix='highvalue')

        if form.is_valid() and setup_formset.is_valid() and topper_formset.is_valid() and highvalue_formset.is_valid():
            form.save()

            for setup_form in setup_formset:
                obj = setup_form.save(commit=False)
                if setup_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive = incentive
                    obj.save()

            for topper_form in topper_formset:
                obj = topper_form.save(commit=False)
                if topper_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive = incentive
                    obj.save()

            for highvalue_form in highvalue_formset:
                obj = highvalue_form.save(commit=False)
                if highvalue_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive = incentive
                    obj.save()

            return redirect('monthlyin_list')
    else:
        form = MonthlyIncentiveForm(instance=incentive)
        setup_formset = SetupSlabFormSet(queryset=SetupChargeRule.objects.filter(incentive=incentive), prefix='setup')
        topper_formset = TopperFormSet(queryset=TopperMonthRule.objects.filter(incentive=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(queryset=HighValueDealSlab.objects.filter(incentive=incentive), prefix='highvalue')

    return render(request, 'owner/monthlyin/monthlyin_form.html', {
        'form': form,
        'setup_formset': setup_formset,
        'topper_formset': topper_formset,
        'highvalue_formset': highvalue_formset,
        'title': 'Update Monthly Incentive'
    })

def monthlyin_list(request):
    incentives = MonthlyIncentive.objects.all()
    return render(request, 'owner/monthlyin/monthlyin_list.html', {'incentives': incentives})


def monthlyin_delete(request, pk):
    incentive = get_object_or_404(MonthlyIncentive, pk=pk)
    if request.method == "POST":
        incentive.delete()
        messages.success(request, "Monthly Incentive deleted successfully.")
        return redirect('monthlyin_list')
    return render(request, 'owner/monthlyin/monthlyin_confirm_delete.html', {'incentive': incentive})


# ---------- Yearly Incentive Views ----------

# List View
def yearlyin_list(request):
    incentives = AnnualTargetIncentive.objects.all()
    return render(request, 'owner/yearlyin/yearlyin_list.html', {'incentives': incentives})

# Create View
def yearlyin_create(request):
    if request.method == 'POST':
        form = YearlyIncentiveForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('yearlyin_list')
    else:
        form = YearlyIncentiveForm()
    return render(request, 'owner/yearlyin/yearlyin_form.html', {
        'form': form,
        'title': 'Create Yearly Incentive',
        'action': 'Create'
    })

# Update View
def yearlyin_update(request, pk):
    incentive = get_object_or_404(AnnualTargetIncentive, pk=pk)
    if request.method == 'POST':
        form = YearlyIncentiveForm(request.POST, instance=incentive)
        if form.is_valid():
            form.save()
            return redirect('yearly_incentive_list')
    else:
        form = YearlyIncentiveForm(instance=incentive)
    return render(request, 'owner/yearlyin/yearlyin_form.html', {
        'form': form,
        'action': 'Update',
        'title': 'Update Yearly Incentive'
    })

# Delete View
def yearlyin_delete(request, pk):
    incentive = get_object_or_404(AnnualTargetIncentive, pk=pk)
    if request.method == 'POST':
        incentive.delete()
        return redirect('yearlyin_list')
    return render(request, 'owner/yearlyin/yearlyin_confirm_delete.html', {
        'incentive': incentive
    })
