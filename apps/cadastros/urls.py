from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # Empresas
    path('empresas/', views.EmpresaListView.as_view(), name='empresa_list'),
    path('empresas/nova/', views.EmpresaCreateView.as_view(), name='empresa_create'),
    path('empresas/<int:pk>/', views.EmpresaDetailView.as_view(), name='empresa_detail'),
    path('empresas/<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='empresa_update'),
    path('empresas/<int:pk>/excluir/', views.EmpresaDeleteView.as_view(), name='empresa_delete'),
    
    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/novo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/excluir/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    
    # Funcionários
    path('funcionarios/', views.FuncionarioListView.as_view(), name='funcionario_list'),
    path('funcionarios/novo/', views.FuncionarioCreateView.as_view(), name='funcionario_create'),
    path('funcionarios/<int:pk>/', views.FuncionarioDetailView.as_view(), name='funcionario_detail'),
    path('funcionarios/<int:pk>/editar/', views.FuncionarioUpdateView.as_view(), name='funcionario_update'),
    path('funcionarios/<int:pk>/excluir/', views.FuncionarioDeleteView.as_view(), name='funcionario_delete'),
    
    # API para busca
    path('api/buscar-cliente-empresa/', views.buscar_cliente_empresa, name='buscar_cliente_empresa'),
]
