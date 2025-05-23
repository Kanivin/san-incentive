from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Login and Logout paths
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('superadmin-dashboard/', views.admin_dashboard, name='superadmin_dashboard'),
    path('accounts-dashboard/', views.accounts_dashboard, name='accounts_dashboard'),
    path('sales-dashboard/', views.sales_dashboard, name='sales_dashboard'),

    # Admin user management
    path('admin-user/', views.user_list, name='user_list'),
    path('user-create/', views.user_create, name='user_create'),
    path('user-edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('user-delete/<int:pk>/', views.user_delete, name='user_delete'),

    # Admin deal management
    path('admin-deal/', views.deal_list, name='deal_list'),
    path('deal-create/', views.deal_create, name='deal_create'),
    path('deal-edit/<int:pk>/', views.deal_update, name='deal_update'),
    path('deal-delete/<int:pk>/', views.deal_delete, name='deal_delete'),

    # Admin Annual Target
    path('admin-target/', views.target_list, name='target_list'),
    path('target-create/', views.target_create, name='target_create'),
    path('target-edit/<int:pk>/', views.target_update, name='target_update'),
    path('target-delete/<int:pk>/', views.target_delete, name='target_delete'),



    # Admin Annual Target
    path('admin-incentives/', views.incentive_setup_list, name='incentive_setup_list'),
    path('incentive_setup-create/', views.incentive_setup_create, name='incentive_setup_create'),
    path('incentive_setup-edit/<int:pk>/', views.incentive_setup_update, name='incentive_setup_update'),
    path('incentive_setup-delete/<int:pk>/', views.incentive_setup_delete, name='incentive_setup_delete'),

    # Admin Segements Target
    path('segments/', views.segment, name='segment'),


     # Admin Leadsource Target   
    path('leadsources/', views.leadsource, name='leadsource'),

    
     # Admin Leadsource Target   
    path('module/', views.module, name='module'),
    path('module/<int:pk>/', views.module, name='module_edit'),

    
     # Admin Leadsource Target   
    path('roles/', views.roles, name='roles'),

    
     # Admin Leadsource Target   
    path('permission/', views.permission, name='permission'),

    path('deal/approve/<int:pk>/', views.deal_approve, name='deal_approve'),

        path('salesteam/', views.salesteam, name='salesteam'),
      path('payout/', views.payout, name='payout'),
        path('transaction/', views.transaction, name='transaction'),
]

