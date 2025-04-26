from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from datetime import datetime
from .models import UserProfile, Deal, Role, Segment, AnnualTarget,Segment, LeadSource,AnnualTargetIncentive, MonthlyIncentive, SetupChargeRule, TopperMonthRule, HighValueDealSlab, Permission, Module,Role,Segment,LeadSource
from .forms import UserProfileForm,LeadSourceForm, SegmentForm,DealForm, AnnualTargetForm, MonthlyIncentiveForm, SetupChargeRuleForm, TopperMonthRuleForm, HighValueDealSlabForm, YearlyIncentiveForm, RoleForm, ModuleForm
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
                user_type = user.user_type.name.lower()

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
            user = form.save(commit=False)
            # If you have a password field, don't forget:
            # user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('user_list')
        else:
            # 🔥 Print the form errors in console
            print("Form errors:", form.errors)
    else:
        form = UserProfileForm()
    
    roles = Role.objects.all()
    return render(request, 'owner/users/user_form.html', {
        'form': form,
        'roles': roles,
        'title': 'Create User',
    })

def user_edit(request, pk):
    user = get_object_or_404(UserProfile, pk=pk)
    roles = Role.objects.all()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'owner/users/user_form.html', {
        'form': form,
        'roles': roles,
        'title': 'Edit User'
    })

def user_delete(request, pk):
    user = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'owner/users/user_confirm_delete.html', {
        'user': user,
        'title': 'Delete User'
    })


# ---------- Deal Management Views ----------

def deal_list(request):
    deals = Deal.objects.all()
    return render(request, 'owner/deal/deal_list.html', {'deals': deals})

def deal_create(request):
    if request.method == 'POST':
        form = DealForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)  # Print the cleaned data for debugging
            form.save()
            return redirect('deal_list')
    else:
        form = DealForm()
        users = UserProfile.objects.filter(user_type__in=['salesperson', 'saleshead'])
        print(users)  # Debug print for users
        return render(request, 'owner/deal/deal_form.html', {
            'form': form,
            'action': 'Create',
            'title': 'Create Deal',
            'users': users
        })
    
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
    current_year = datetime.now().year
    financial_years = [f"{year}-{year + 1}" for year in range(current_year, current_year + 11)]
    segments = Segment.objects.all()
    if request.method == 'POST':
        form = MonthlyIncentiveForm(request.POST)
        if form.is_valid():
            monthly_incentive = form.save()

            # Save SetupChargeRules
            min_amounts = request.POST.getlist('setup_min_amount[]')
            max_amounts = request.POST.getlist('setup_max_amount[]')
            incentive_percentages = request.POST.getlist('setup_incentive_percentage[]')

            for min_amt, max_amt, inc_perc in zip(min_amounts, max_amounts, incentive_percentages):
                SetupChargeRule.objects.create(
                    rule_set=monthly_incentive,
                    min_amount=min_amt or 0,
                    max_amount=max_amt or 0,
                    incentive_percentage=inc_perc or 0
                )

            # Save TopperMonthRules
            topper_segments = request.POST.getlist('topper_segment[]')
            min_subs = request.POST.getlist('topper_min_subscription[]')
            incentives = request.POST.getlist('topper_incentive_percentage[]')

            for segment_id, min_sub, inc_perc in zip(topper_segments, min_subs, incentives):
                if segment_id:  # Only if segment is selected
                    TopperMonthRule.objects.create(
                        rule_set=monthly_incentive,
                        segment_id=segment_id,
                        min_subscription=min_sub or 0,
                        incentive_percentage=inc_perc or 0
                    )

            # Save HighValueDealSlabs
            min_values = request.POST.getlist('high_value_min_amount[]')
            max_values = request.POST.getlist('high_value_max_amount[]')
            high_value_incentives = request.POST.getlist('high_value_incentive_percentage[]')

            for min_val, max_val, inc_perc in zip(min_values, max_values, high_value_incentives):
                HighValueDealSlab.objects.create(
                    rule_set=monthly_incentive,
                    min_amount=min_val or 0,
                    max_amount=max_val or 0,
                    incentive_percentage=inc_perc or 0
                )

            return redirect('monthlyin_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = MonthlyIncentiveForm()

    return render(request, 'owner/monthlyin/monthlyin_form.html', {
        'form': form,
        'financial_years': financial_years,
        'title':'Create Monthly Incentive Setup',
        'segments': segments,
    })


def monthlyin_update(request, pk):
    incentive = get_object_or_404(MonthlyIncentive, pk=pk)
    current_year = datetime.now().year
    financial_years = [f"{year}-{year + 1}" for year in range(current_year, current_year + 11)]
    
    # Use modelformset_factory to create formsets
    SetupSlabFormSet = modelformset_factory(SetupChargeRule, form=SetupChargeRuleForm, extra=0, can_delete=True)
    TopperFormSet = modelformset_factory(TopperMonthRule, form=TopperMonthRuleForm, extra=0, can_delete=True)
    HighValueFormSet = modelformset_factory(HighValueDealSlab, form=HighValueDealSlabForm, extra=0, can_delete=True)

    if request.method == 'POST':
        form = MonthlyIncentiveForm(request.POST, instance=incentive)
        
        # Initialize formsets with POST data and prefixes
        setup_formset = SetupSlabFormSet(request.POST, queryset=SetupChargeRule.objects.filter(rule_set=incentive), prefix='setup')
        topper_formset = TopperFormSet(request.POST, queryset=TopperMonthRule.objects.filter(rule_set=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(request.POST, queryset=HighValueDealSlab.objects.filter(rule_set=incentive), prefix='highvalue')

        if form.is_valid() and setup_formset.is_valid() and topper_formset.is_valid() and highvalue_formset.is_valid():
            form.save()

            # Save SetupSlab formset
            for setup_form in setup_formset:
                obj = setup_form.save(commit=False)
                if setup_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.rule_set = incentive
                    obj.save()

            # Save TopperMonthRule formset
            for topper_form in topper_formset:
                obj = topper_form.save(commit=False)
                if topper_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.rule_set = incentive
                    obj.save()

            # Save HighValueDealSlab formset
            for highvalue_form in highvalue_formset:
                obj = highvalue_form.save(commit=False)
                if highvalue_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.rule_set = incentive
                    obj.save()

            return redirect('monthlyin_list')
    else:
        form = MonthlyIncentiveForm(instance=incentive)

        # Initialize formsets for GET request
        setup_formset = SetupSlabFormSet(queryset=SetupChargeRule.objects.filter(rule_set=incentive), prefix='setup')
        topper_formset = TopperFormSet(queryset=TopperMonthRule.objects.filter(rule_set=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(queryset=HighValueDealSlab.objects.filter(rule_set=incentive), prefix='highvalue')

    # No matter POST or GET, always load slabs separately
    high_value_slabs = HighValueDealSlab.objects.filter(rule_set=incentive)
    topper_month_slabs = TopperMonthRule.objects.filter(rule_set=incentive)
    setup_formset_slabs = SetupChargeRule.objects.filter(rule_set=incentive)

    return render(request, 'owner/monthlyin/monthlyin_form.html', {
        'form': form,
        'setup_formset': setup_formset,
        'topper_formset': topper_formset,
        'highvalue_formset': highvalue_formset,
        'high_value_slabs': high_value_slabs,
        'topper_month_slabs':topper_month_slabs,
        'setup_formset_slabs':setup_formset_slabs,
        'financial_years': financial_years,
        'title': 'Update Monthly Incentive'
    })

def monthlyin_list(request):
    incentives = MonthlyIncentive.objects.all()
    return render(request, 'owner/monthlyin/monthlyin_list.html', {'monthly_incentives': incentives})


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


def module(request):
    modules = Module.objects.all()

    edit_id = request.GET.get('edit')
    if edit_id:
        instance = get_object_or_404(Module, pk=edit_id)
    else:
        instance = None

    if request.method == 'POST':
        # Check for delete
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            Module.objects.filter(pk=delete_id).delete()
            return redirect('module')  # After delete, clean reload

        # Else, handle save
        form = ModuleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('module')  # After save, clean reload
    else:
        form = ModuleForm(instance=instance)

    return render(request, 'owner/settings/module.html', {
        'modules': modules,  # <<< correct name (small m)
        'form': form,
        'editing': bool(edit_id),
    })

def segment(request):
    edit_id = request.GET.get('edit')
    delete_id = request.POST.get('delete_id')

    # Handle Delete
    if delete_id:
        segment = get_object_or_404(Segment, id=delete_id)
        segment.delete()
        messages.success(request, "Segment deleted successfully.")
        return redirect('segment')  # Update with your url name

    # Handle Create or Edit
    if edit_id:
        segment = get_object_or_404(Segment, id=edit_id)
    else:
        segment = Segment()

    if request.method == 'POST' and not delete_id:
        form = SegmentForm(request.POST, instance=segment)
        if form.is_valid():
            form.save()
            messages.success(request, "Segment saved successfully.")
            return redirect('segment')  # Update with your url name
    else:
        form = SegmentForm(instance=segment)

    segments = Segment.objects.all()

    return render(request, 'owner/master/segment.html', {
        'form': form,
        'Segments': segments,
        'title': 'Add/Edit Segment',
        'button_label': 'Save Segment'
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import LeadSource
from .forms import LeadSourceForm

def leadsource(request):
    edit_id = request.GET.get('edit')  # fetch edit id from query params

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            # Handle Delete
            delete_id = request.POST.get('delete_id')
            leadsource = get_object_or_404(LeadSource, pk=delete_id)
            leadsource.delete()
            return redirect('leadsource')  # Make sure your URL name is correct
        else:
            # Handle Create or Update
            leadsource_id = request.POST.get('id')
            instance = LeadSource.objects.filter(pk=leadsource_id).first() if leadsource_id else None
            form = LeadSourceForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                return redirect('leadsource')
    else:
        # GET Request
        instance = LeadSource.objects.filter(pk=edit_id).first() if edit_id else None
        form = LeadSourceForm(instance=instance)

    lead_sources = LeadSource.objects.all()

    return render(request, 'owner/master/leadsource.html', {
        'form': form,
        'lead_sources': lead_sources,  # <- fixed from 'roles' to 'lead_sources'
        'title': 'Manage Lead Source',
        'button_label': 'Update' if edit_id else 'Save',
    })

def roles(request):
    edit_id = request.GET.get('edit')  # fetch edit id from query params if any

    if request.method == 'POST':
        if 'delete_id' in request.POST:  # Delete operation
            delete_id = request.POST.get('delete_id')
            role = get_object_or_404(Role, pk=delete_id)
            role.delete()
            return redirect('roles')
        else:  # Create or Update operation
            role_id = request.POST.get('id')
            instance = Role.objects.filter(pk=role_id).first() if role_id else None
            form = RoleForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                return redirect('roles')
    else:
        instance = Role.objects.filter(pk=edit_id).first() if edit_id else None
        form = RoleForm(instance=instance)

    roles = Role.objects.all()
    return render(request, 'owner/settings/roles.html', {
        'form': form,
        'roles': roles,
        'title': 'Manage Roles',
        'button_label': 'Update' if edit_id else 'Save',
    })

def permission(request):
    roles = Role.objects.all()
    modules = Module.objects.all()

    if request.method == 'POST':
        # Clear old permissions if needed
        Permission.objects.all().delete()

        for role in roles:
            for module in modules:
                can_add = bool(request.POST.get(f'permissions_{role.id}_{module.id}_add'))
                can_edit = bool(request.POST.get(f'permissions_{role.id}_{module.id}_edit'))
                can_delete = bool(request.POST.get(f'permissions_{role.id}_{module.id}_delete'))
                can_view = bool(request.POST.get(f'permissions_{role.id}_{module.id}_view'))

                if can_add or can_edit or can_delete or can_view:
                    Permission.objects.update_or_create(
                        role=role,
                        module=module,
                        defaults={
                            'can_add': can_add,
                            'can_edit': can_edit,
                            'can_delete': can_delete,
                            'can_view': can_view,
                        }
                    )

        return redirect('permission')  # make sure your urls.py has name='permission'

    # GET request
    permissions = Permission.objects.all()
    permission_matrix = {}

    for permission in permissions:
        permission_matrix.setdefault(permission.role_id, {})[permission.module_id] = {
            'can_add': permission.can_add,
            'can_edit': permission.can_edit,
            'can_delete': permission.can_delete,
            'can_view': permission.can_view,
        }

    return render(request, 'owner/settings/permissions.html', {
        'roles': roles,
        'modules': modules,
        'permission_matrix': permission_matrix,
    })