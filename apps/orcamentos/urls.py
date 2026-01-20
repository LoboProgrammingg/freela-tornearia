from django.urls import path
from . import views

app_name = 'orcamentos'

urlpatterns = [
    path('', views.OrcamentoListView.as_view(), name='orcamento_list'),
    path('novo/', views.OrcamentoCreateView.as_view(), name='orcamento_create'),
    path('<int:pk>/', views.OrcamentoDetailView.as_view(), name='orcamento_detail'),
    path('<int:pk>/editar/', views.OrcamentoUpdateView.as_view(), name='orcamento_update'),
    path('<int:pk>/excluir/', views.OrcamentoDeleteView.as_view(), name='orcamento_delete'),
    path('<int:pk>/pdf/', views.gerar_pdf_orcamento, name='orcamento_pdf'),
    path('<int:pk>/aprovar/', views.aprovar_orcamento, name='orcamento_aprovar'),
    path('<int:pk>/rejeitar/', views.rejeitar_orcamento, name='orcamento_rejeitar'),
    path('<int:pk>/converter/', views.converter_orcamento_venda, name='orcamento_converter'),
]
