from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from datetime import datetime
from .models import UserProfile, Deal, Role, Segment, Module, AnnualTarget, IncentiveSetup, SetupChargeSlab, TopperMonthSlab, HighValueDealSlab, Permission
from .forms import UserProfileForm, SegmentForm,DealForm, AnnualTargetForm,  RoleForm, ModuleForm, IncentiveSetupForm, SetupChargeSlabForm, TopperMonthSlabForm, HighValueDealSlabForm
from django.forms import modelformset_factory
from decimal import Decimal
import json
from django.db.models import Count
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
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DealForm
from .models import Deal, UserProfile
from pprint import pprint

def deal_list(request):
    deals = Deal.objects.all()

    # Manually convert date fields to string to avoid JSON serialization errors
    for deal in deals:
        if deal.dealWonDate:
            deal.dealWonDate = deal.dealWonDate.isoformat()  # Convert to string (iso format)

    return render(request, 'owner/deal/deal_list.html', {'deals': deals})

def deal_create(request):
    # Fetch users with user_type 'salesperson' or 'saleshead'
    users = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])

    if request.method == 'POST':
        form = DealForm(request.POST)

        if form.is_valid():
            deal = form.save(commit=False)

            # Save the deal instance
            deal.save()
            return redirect('deal_list')  # Success: redirect to deal list
        else:
            # For safe debugging without JSON serialization issues
            pprint(form.errors)
            # You can also safely view cleaned_data as a dict:
            # pprint({k: str(v) if isinstance(v, date) else v for k, v in form.cleaned_data.items()})

    else:
        form = DealForm()

    return render(request, 'owner/deal/deal_form.html', {
        'form': form,
        'action': 'Create',
        'title': 'Create Deal',
        'users': users,
    })

def deal_update(request, pk):
    deal = get_object_or_404(Deal, pk=pk)

    # Fetch the users that are either salesperson or saleshead
    users = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])

    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            form.save()
            return redirect('deal_list')
        else:
            print(form.errors)  # Optional: Debugging form errors
    else:
        form = DealForm(instance=deal)

    return render(request, 'owner/deal/deal_form.html', {
        'form': form,
        'action': 'Update',
        'title': 'Update Deal',
        'deal': deal,
        'users': users,  # Pass users to populate dropdowns
    })

def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        deal.delete()
        return redirect('deal_list')
    return render(request, 'owner/deal/deal_confirm_delete.html', {'deal': deal})

# ---------- Annual Target Views ----------

def target_list(request):
    # Step 1: Fetch all records ordered by employee and financial year
    targets = AnnualTarget.objects.all().order_by('employee', 'financial_year')
    
    # Step 2: Manually filter out duplicates based on employee and financial year
    unique_targets = []
    seen = set()
    
    for target in targets:
        # Create a tuple of employee ID and financial year to check uniqueness
        identifier = (target.employee.id, target.financial_year)
        
        if identifier not in seen:
            unique_targets.append(target)
            seen.add(identifier)

    # Pass the filtered unique targets to the template
    return render(request, 'owner/annual_target/target_list.html', {'targets': unique_targets})


    
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Or use float(obj) to convert to float instead of string
        return super().default(obj)

def target_create(request):
    users = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])
    if request.method == 'POST':
        form = AnnualTargetForm(request.POST)
        if form.is_valid():
            # Log the form data before saving
            print("Form data:", form.cleaned_data)
            annual_target = form.save()
            print(f"Annual target saved: {annual_target}")  # Log the saved instance
            return redirect('target_list')
        else:
            print("Form errors:", form.errors)  # Log form errors
            return render(request, 'owner/annual_target/target_form.html', {
                'form': form,
                'users': users,
                'financial_years': generate_financial_years(),
                'title': 'Create Annual Target',
                'action': 'Create'
            })
    else:
        form = AnnualTargetForm()

    return render(request, 'owner/annual_target/target_form.html', {
        'form': form,
        'users': users,
        'financial_years': generate_financial_years(),
        'title': 'Create Annual Target',
        'action': 'Create'
    })

def target_update(request, pk):
    target = get_object_or_404(AnnualTarget, pk=pk)
    users = UserProfile.objects.filter(user_type__name__in=['salesperson', 'saleshead'])
    if request.method == 'POST':
        form = AnnualTargetForm(request.POST, instance=target)
        if form.is_valid():
            # Save the form if it's valid
            form.save()
            return redirect('target_list')  # Redirect after saving
    else:
        form = AnnualTargetForm(instance=target)

    return render(request, 'owner/annual_target/target_form.html', {
        'form': form,
        'action': 'Update',
        'target': target,
        'users': users,
        'financial_years': generate_financial_years(),
        'title': 'Update Annual Target'
    })
def target_delete(request, pk):
    target = get_object_or_404(AnnualTarget, pk=pk)
    if request.method == 'POST':
        target.delete()
        return redirect('target_list')
    return render(request, 'owner/annual_target/target_confirm_delete.html', {'target': target})

def generate_financial_years():
    current_year = datetime.now().year
    return [f"{year}-{year + 1}" for year in range(current_year, current_year + 11)]


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
from django.shortcuts import render, redirect
from datetime import datetime
from .forms import IncentiveSetupForm
from .models import IncentiveSetup, SetupChargeSlab, TopperMonthSlab, HighValueDealSlab, Segment

def incentive_setup_create(request):
    current_year = datetime.now().year
    financial_years = [f"{year}-{year + 1}" for year in range(current_year, current_year + 11)]
    months = [month for month in range(1, 13)]
    segments = Segment.objects.all()

    if request.method == 'POST':
        form = IncentiveSetupForm(request.POST)
        if form.is_valid():
            monthly_incentive = form.save()

            # ✅ Save SetupChargeSlabs with deal_type_setup
            deal_type_setup = request.POST.getlist('deal_type_setup[]')
            min_amounts = request.POST.getlist('setup_min_amount[]')
            max_amounts = request.POST.getlist('setup_max_amount[]')
            incentive_percentages = request.POST.getlist('setup_incentive_percentage[]')

            for deal_type, min_amt, max_amt, inc_perc in zip(deal_type_setup, min_amounts, max_amounts, incentive_percentages):
                SetupChargeSlab.objects.create(
                    incentive_setup=monthly_incentive,
                    deal_type_setup=deal_type,  # <-- This was missing
                    min_amount=min_amt or 0,
                    max_amount=max_amt or 0,
                    incentive_percentage=inc_perc or 0
                )

            # ✅ Save TopperMonthSlabs
            deal_type_top = request.POST.getlist('deal_type_top[]')
            topper_segments = request.POST.getlist('segment[]')
            min_subs = request.POST.getlist('min_subscription[]')
            incentives = request.POST.getlist('incentive_percentage[]')

            for deal_type, segment_id, min_sub, inc_perc in zip(deal_type_top,topper_segments, min_subs, incentives):
                if segment_id:
                    TopperMonthSlab.objects.create(
                        incentive_setup=monthly_incentive,
                        deal_type_top=deal_type,
                        segment_id=segment_id,
                        min_subscription=min_sub or 0,
                        incentive_percentage=inc_perc or 0
                    )

            # ✅ Save HighValueDealSlabs
            deal_types_high = request.POST.getlist('deal_type_high[]')
            min_values = request.POST.getlist('high_value_min_amount[]')
            max_values = request.POST.getlist('high_value_max_amount[]')
            high_value_incentives = request.POST.getlist('high_value_incentive_percentage[]')

            for deal_type, min_val, max_val, inc_perc in zip(deal_types_high, min_values, max_values, high_value_incentives):
                HighValueDealSlab.objects.create(
                    incentive_setup=monthly_incentive,
                    deal_type_high=deal_type,
                    min_amount=min_val or 0,
                    max_amount=max_val or 0,
                    incentive_percentage=inc_perc or 0
                )

            return redirect('incentive_setup_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = IncentiveSetupForm()

    return render(request, 'owner/incentive_setup/incentive_setup_form.html', {
        'form': form,
        'financial_years': financial_years,
        'title': 'Create Incentive Setup',
        'months': months,
        'segments': segments,
    })

def incentive_setup_update(request, pk):
    # Fetch the IncentiveSetup instance or 404 if not found
    incentive = get_object_or_404(IncentiveSetup, pk=pk)

    # Financial year options (next 10 years from current year)
    current_year = datetime.now().year
    financial_years = [f"{year}-{year + 1}" for year in range(current_year, current_year + 11)]
    segments = Segment.objects.all()
    months = [month for month in range(1, 13)]
    # Modelformset factories for formsets
    SetupSlabFormSet = modelformset_factory(SetupChargeSlab, form=SetupChargeSlabForm, extra=0, can_delete=True)
    TopperFormSet = modelformset_factory(TopperMonthSlab, form=TopperMonthSlabForm, extra=0, can_delete=True)
    HighValueFormSet = modelformset_factory(HighValueDealSlab, form=HighValueDealSlabForm, extra=0, can_delete=True)

    if request.method == 'POST':
        # Main form for IncentiveSetup
        print(request.POST)
        form = IncentiveSetupForm(request.POST, instance=incentive)
        
        # Initialize formsets with POST data and prefixes
        setup_formset = SetupSlabFormSet(request.POST, queryset=SetupChargeSlab.objects.filter(incentive_setup=incentive), prefix='setup')
        topper_formset = TopperFormSet(request.POST, queryset=TopperMonthSlab.objects.filter(incentive_setup=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(request.POST, queryset=HighValueDealSlab.objects.filter(incentive_setup=incentive), prefix='highvalue')

        # Check if all forms and formsets are valid
        if form.is_valid() and setup_formset.is_valid() and topper_formset.is_valid() and highvalue_formset.is_valid():
            # Save the main IncentiveSetup form
            form.save()

            # Save or delete records in SetupSlab formset
            for setup_form in setup_formset:
                obj = setup_form.save(commit=False)
                if setup_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive_setup = incentive
                    obj.save()

            # Save or delete records in TopperMonthSlab formset
            for topper_form in topper_formset:
                obj = topper_form.save(commit=False)
                if topper_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive_setup = incentive
                    obj.save()

            # Save or delete records in HighValueDealSlab formset
            for highvalue_form in highvalue_formset:
                obj = highvalue_form.save(commit=False)
                if highvalue_form.cleaned_data.get('DELETE'):
                    if obj.pk:
                        obj.delete()
                else:
                    obj.incentive_setup = incentive
                    obj.save()

            messages.success(request, "Incentive Setup updated successfully.")
            return redirect('incentive_setup_list')
        else:
            print("Form errors:")
            print("IncentiveSetupForm errors:", form.errors)
            print("SetupSlabFormSet errors:")
        for f in setup_formset:
            print(f.errors)

        print("TopperMonthSlabFormSet errors:")
        for f in topper_formset:
            print(f.errors)

        print("HighValueDealSlabFormSet errors:")
        for f in highvalue_formset:
            print(f.errors)

        print("Non-form errors:")
        print("SetupSlabFormSet non-form errors:", setup_formset.non_form_errors())
        print("TopperFormSet non-form errors:", topper_formset.non_form_errors())
        print("HighValueFormSet non-form errors:", highvalue_formset.non_form_errors())

    else:
        # GET request, initialize form and formsets with existing data
        form = IncentiveSetupForm(instance=incentive)

        setup_formset = SetupSlabFormSet(queryset=SetupChargeSlab.objects.filter(incentive_setup=incentive), prefix='setup')
        topper_formset = TopperFormSet(queryset=TopperMonthSlab.objects.filter(incentive_setup=incentive), prefix='topper')
        highvalue_formset = HighValueFormSet(queryset=HighValueDealSlab.objects.filter(incentive_setup=incentive), prefix='highvalue')

    # Fetch all relevant slabs for rendering
    high_value_slabs = HighValueDealSlab.objects.filter(incentive_setup=incentive)
    topper_month_slabs = TopperMonthSlab.objects.filter(incentive_setup=incentive)
    setup_formset_slabs = SetupChargeSlab.objects.filter(incentive_setup=incentive)

    return render(request, 'owner/incentive_setup/incentive_setup_form.html', {
        'form': form,
        'setup_formset': setup_formset,
        'topper_formset': topper_formset,
        'highvalue_formset': highvalue_formset,
        'high_value_slabs': high_value_slabs,
        'topper_month_slabs': topper_month_slabs,
        'setup_formset_slabs': setup_formset_slabs,
        'segments':segments,
        'financial_years': financial_years,
        'months':months,
        'title': 'Update Incentive Setup'
    })

def incentive_setup_list(request):
    # List all IncentiveSetups
    incentives = IncentiveSetup.objects.all()
    return render(request, 'owner/incentive_setup/incentive_setup_list.html', {'incentives': incentives})

def incentive_setup_delete(request, pk):
    # Get the IncentiveSetup or 404
    incentive = get_object_or_404(IncentiveSetup, pk=pk)
    
    if request.method == "POST":
        # Delete the incentive setup
        incentive.delete()
        messages.success(request, "Monthly Incentive deleted successfully.")
        return redirect('incentive_setup_list')

    # Confirmation page to delete
    return render(request, 'owner/incentive_setup/incentive_setup_confirm_delete.html', {'incentive': incentive})