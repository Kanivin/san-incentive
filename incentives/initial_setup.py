from incentives.models import Role, Module, Permission, UserProfile
from django.utils.timezone import now

# Create roles
roles = {
    'superadmin': False,
    'admin': True,
    'accounts': True,
    'salesperson': True,
    'saleshead': True
}



# Assuming roles is a dictionary of roles and their selectable status
for name, selectable in roles.items():
    Role.objects.get_or_create(name=name, defaults={'is_selectable': selectable})


# Create modules
modules = ['Users', 'Deals', 'Annual Tragets', 'Roles', 'Site Settings', 'Permissions','Lead Sources','Segments','Modules','Monthly Incentive Setup','Yearly Incentive Setup']
for mod in modules:
    Module.objects.get_or_create(module=mod)
    
# Give full permission to superadmin
superadmin_role = Role.objects.get(name='superadmin')
for mod in Module.objects.all():
    Permission.objects.get_or_create(
        role=superadmin_role,
        module=mod,  # use the actual field name
        defaults={
            'can_add': True,
            'can_edit': True,
            'can_delete': True,
            'can_view': True
        }
    )

# Create superadmin user profile
superadmin_profile, created = UserProfile.objects.update_or_create(
    mail_id='info.kanivin@gmail.com',
    defaults={
        'fullname': 'kanivin',
        'phone': '9445532899',
        'password': 'kanivin2025',  # ensure password is hashed when saving
        'user_type': superadmin_role,
        'doj': now().date(),
        'employee_id': 'EMP0001',
        'enable_login': True
    }
)

if created:
    print(f'Superadmin profile created: {superadmin_profile}')
else:
    print(f'Superadmin profile updated: {superadmin_profile}')
