from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Login and Logout paths
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
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
    path('admin-yearlyin/', views.yearlyin_list, name='yearlyin_list'),
    path('yearlyin-create/', views.yearlyin_create, name='yearlyin_create'),
    path('yearlyin-edit/<int:pk>/', views.yearlyin_update, name='yearlyin_update'),
    path('yearlyin-delete/<int:pk>/', views.yearlyin_delete, name='yearlyin_delete'),

    # Admin Annual Target
    path('admin-monthlyin/', views.monthlyin_list, name='monthlyin_list'),
    path('monthlyin-create/', views.monthlyin_create, name='monthlyin_create'),
    path('monthlyin-edit/<int:pk>/', views.monthlyin_update, name='monthlyin_update'),
    path('monthlyin-delete/<int:pk>/', views.monthlyin_delete, name='monthlyin_delete'),

    # Admin Segements Target
    path('segments/', views.segment_list, name='segment_list'),
    path('segments/create/', views.segment_create, name='segment_create'),
    path('segments/edit/<int:pk>/', views.segment_edit, name='segment_edit'),
    path('segments/delete/<int:pk>/', views.segment_delete, name='segment_delete'),

     # Admin Leadsource Target   
    path('leadsources/', views.leadsource_list, name='leadsource_list'),
    path('leadsources/create/', views.leadsource_create, name='leadsource_create'),
    path('leadsources/edit/<int:pk>/', views.leadsource_edit, name='leadsource_edit'),
    path('leadsources/delete/<int:pk>/', views.leadsource_delete, name='leadsource_delete'),
    
]

