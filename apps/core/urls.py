from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('configuracao/', views.ConfiguracaoEmpresaView.as_view(), name='configuracao'),
    path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
]
