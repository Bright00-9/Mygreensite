from django.urls import path
from . import views
from django.core.management import call_command
import logging

app_name='dashboard'


# This runs the MOMENT the app starts on Render
try:
    print("FORCE MIGRATION STARTING...")
    # This creates the 'author_id' column if it's missing
    call_command('makemigrations', 'dashboard', interactive=False)
    call_command('migrate', 'dashboard', interactive=False)
    print("FORCE MIGRATION SUCCESSFUL!")
except Exception as e:
    print(f"FORCE MIGRATION ERROR: {e}")

urlpatterns = [
    path('', views.dashboard_home, name='mainboard'),
    path('account/<int:pk>/shield/', views.shield_view, name='shield'),
    path('forum/', views.forum_view, name='forum'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('rightsize/<int:res_id>/', views.api_rightsize, name='rightsize'),
    path('export/', views.generate_pdf_report, name='export'),
    path('dashboard/', views.finops_dashboard, name='finops_dashboard'),
    path('connect-aws/', views.connect_aws, name='connect_aws'),
    path('run_manual_scan/', views.run_manual_scan, name='run_manual_scan'),
    path('terminate/<int:zombie_id>/', views.terminate_resource, name='terminate_resource'),
    path('account/<int:pk>/disconnect/', views.disconnect_cloud, name='disconnect_cloud'),
]

