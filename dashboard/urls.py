from django.urls import path
from . import views

app_name='dashboard'
from django.core.management import call_command
import logging

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
    path('', views.dashboard_view, name='mainboard'),
    path('zombies/', views.zombie_hunter, name='zombies'),
    path('shield/', views.shield_view, name='shield'),
    path('forum/', views.forum_view, name='forum'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('rightsize/<int:res_id>/', views.api_rightsize, name='rightsize'),
    path('export/', views.download_report, name='export'),
    path('dashboard/', views.finops_dashboard, name='finops_dashboard'),
]

