from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='item_list'),
    path('novo/', views.ItemCreateView.as_view(), name='item_create'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('<int:pk>/editar/', views.ItemUpdateView.as_view(), name='item_update'),
    path('<int:pk>/excluir/', views.ItemDeleteView.as_view(), name='item_delete'),
    
    # APIs
    path('api/buscar/', views.buscar_itens, name='buscar_itens'),
    path('api/<int:pk>/preco/', views.obter_preco_item, name='obter_preco_item'),
]
