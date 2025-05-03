from incentives.models import Role, Module, Permission, UserProfile
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password

# Define roles and whether they are selectable by users
from incentives.models import Role, Module
roles = {
    'superadmin': False,
    'admin': True,
    'accounts': True,
    'salesperson': True,
    'saleshead': True
}

# Make sure this runs cleanly
for name, selectable in roles.items():
    Role.objects.get_or_create(name=name, defaults={'is_selectable': selectable})


# Define modules (only one Incentive Setup, no Monthly or Yearly)
modules = [
    'Users', 'Deals', 'Annual Targets', 'Roles', 'Site Settings',
    'Permissions', 'Lead Sources', 'Segments', 'Modules',
    'IncentiveSetup'
]

# Create modules
for mod in modules:
    obj, created = Module.objects.get_or_create(module=mod.strip())


# Get superadmin role
superadmin_role = Role.objects.get(name='superadmin')

# Assign full permissions to superadmin for all modules
for mod in Module.objects.all():
    Permission.objects.get_or_create(
        role=superadmin_role,
        module=mod,
        defaults={
            'can_add': True,
            'can_edit': True,
            'can_delete': True,
            'can_view': True
        }
    )

# Create or update superadmin user
superadmin_profile, created = UserProfile.objects.update_or_create(
    mail_id='info.kanivin@gmail.com',
    defaults={
        'fullname': 'kanivin',
        'phone': '9445532899',
        'password': make_password('kanivin2025'),  # hashed password
        'user_type': superadmin_role,
        'doj': now().date(),
        'employee_id': 'EMP0001',
        'enable_login': True
    }
)

# Output result
print(f'Superadmin profile {"created" if created else "updated"}: {superadmin_profile}')
