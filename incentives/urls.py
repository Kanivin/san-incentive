from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Login and Logout paths
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Dashboards
    
    #path('dashboard-router/', views.dashboard_router, name='dashboard_router'),
    #path('admin-dashboard/', views.dashboard_router, name='dashboard_router'),
    #path('superadmin-dashboard/', views.dashboard_router, name='dashboard_router'),
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    #path('sales-dashboard/', views.sales_dashboard, name='sales_dashboard'),

    # Admin user management
    path('admin-user/', views.user_list, name='user_list'),
    path('user-create/', views.user_create, name='user_create'),
    path('user-edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('user-delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('users/export/xlsx/', views.export_users_xlsx, name='user_export_xlsx'),
    path('users/export/pdf/', views.export_users_pdf, name='user_export_pdf'),
    # Admin deal management
    path('admin-deal/', views.deal_list, name='deal_list'),
    path('deal-create/', views.deal_create, name='deal_create'),
     path('deal-view/<int:pk>/', views.deal_view, name='deal_view'),
    path('deal-edit/<int:pk>/', views.deal_update, name='deal_update'),
    path('deal-delete/<int:pk>/', views.deal_delete, name='deal_delete'),
        path('deals/export/excel/', views.deal_export_excel, name='deal_export_excel'),
    path('deals/export/pdf/', views.deal_export_pdf, name='deal_export_pdf'),

    # Admin Annual Target
    path('admin-target/', views.target_list, name='target_list'),
    path('target-create/', views.target_create, name='target_create'),
    path('target-edit/<int:pk>/', views.target_update, name='target_update'),
    path('target-delete/<int:pk>/', views.target_delete, name='target_delete'),
    path('annual-targets/export/excel/', views.target_export_excel, name='target_export_excel'),
    path('annual-targets/export/pdf/', views.target_export_pdf, name='target_export_pdf'),



    # Admin Annual Target
    path('admin-incentives/', views.incentive_setup_list, name='incentive_setup_list'),
    path('incentive_setup-create/', views.incentive_setup_create, name='incentive_setup_create'),
    path('incentive_setup-view/<int:pk>/', views.incentive_setup_view, name='incentive_setup_view'),
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
    path('transaction/export/excel/', views.transaction_export_excel, name='transaction_export_excel'),
    path('transaction/export/pdf/', views.transaction_export_pdf, name='transaction_export_pdf'),
    path('targettransaction/', views.targettransaction, name='targettransaction'),
    path('targettransaction/export/excel/', views.targettransaction_export_excel, name='targettransaction_export_excel'),
    path('targettransaction/export/pdf/', views.targettransaction_export_pdf, name='targettransaction_export_pdf'),
    path("backup_db/", views.backup_db_view, name="backup_db"),

    path('run-now/<str:job>/', views.run_now, name='run_now'),
    path('run-now/<str:job>/<str:runmonth>', views.run_now, name='run_now'),
    path('schedulelog/', views.schedulelog, name='schedulelog'),
    path('changelog/', views.changelog, name='changelog'),
    path('payout/mark-paid/<int:payout_id>/', views.mark_payout_paid, name='mark_payout_paid'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

