
from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('users/', include('users.urls')),
    path('dashboard/', include('dashboard.urls'))
]
admin.site.idex_title="KOMADO"
admin.site.site_hearder="Komado Admin Center"
admin.site.site_title=""