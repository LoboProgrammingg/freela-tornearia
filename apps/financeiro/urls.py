from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Vendas
    path('vendas/', views.VendaListView.as_view(), name='venda_list'),
    path('vendas/nova/', views.VendaCreateView.as_view(), name='venda_create'),
    path('vendas/<int:pk>/', views.VendaDetailView.as_view(), name='venda_detail'),
    path('vendas/<int:pk>/editar/', views.VendaUpdateView.as_view(), name='venda_update'),
    path('vendas/<int:pk>/excluir/', views.VendaDeleteView.as_view(), name='venda_delete'),
    path('vendas/<int:pk>/concluir/', views.concluir_venda, name='venda_concluir'),
    path('vendas/<int:pk>/cancelar/', views.cancelar_venda, name='venda_cancelar'),
    path('vendas/<int:pk>/comprovante/', views.gerar_comprovante_venda, name='venda_comprovante'),
    path('vendas/<int:pk>/gerar-parcelas/', views.gerar_parcelas_venda, name='venda_gerar_parcelas'),
    
    # Parcelas
    path('parcelas/<int:pk>/pagar/', views.marcar_parcela_paga, name='parcela_pagar'),
    
    # Folha de Pagamento
    path('folha-pagamento/', views.FolhaPagamentoListView.as_view(), name='folha_list'),
    path('folha-pagamento/gerar/', views.gerar_folha_pagamento, name='folha_gerar'),
    path('folha-pagamento/<int:pk>/processar/', views.processar_folha_pagamento, name='folha_processar'),
    
    # Despesas
    path('despesas/', views.DespesaListView.as_view(), name='despesa_list'),
    path('despesas/nova/', views.DespesaCreateView.as_view(), name='despesa_create'),
    path('despesas/<int:pk>/editar/', views.DespesaUpdateView.as_view(), name='despesa_update'),
    path('despesas/<int:pk>/excluir/', views.DespesaDeleteView.as_view(), name='despesa_delete'),
    
    # Categorias
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nova/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
]
