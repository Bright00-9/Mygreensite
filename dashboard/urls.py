from django.urls import path
from . import views

app_name='dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='mainboard'),
    path('zombies/', views.zombie_hunter, name='zombies'),
    path('shield/', views.shield_view, name='shield'),
    path('forum/', views.forum_view, name='forum'),
    path('<int:id>/delete/', views.post_delete, name='delete'),
    path('rightsize/<int:res_id>/', views.api_rightsize, name='rightsize'),
    path('export/', views.download_report, name='export'),
    path('dashboard/', views.finops_dashboard, name='finops_dashboard'),
]

