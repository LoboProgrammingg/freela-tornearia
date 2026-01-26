"""
Configuração de URLs do projeto Tornearia Jair.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.core.views import healthcheck

urlpatterns = [
    path('health/', healthcheck, name='healthcheck'),
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('cadastros/', include('apps.cadastros.urls')),
    path('servicos/', include('apps.servicos.urls')),
    path('orcamentos/', include('apps.orcamentos.urls')),
    path('financeiro/', include('apps.financeiro.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
