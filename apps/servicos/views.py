from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .models import Item


class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'servicos/item_list.html'
    context_object_name = 'itens'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        tipo = self.request.GET.get('tipo')
        
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(descricao__icontains=busca)
            )
        if tipo:
            queryset = queryset.filter(tipo=tipo)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_filtro'] = self.request.GET.get('tipo', '')
        context['itens_estoque_baixo'] = Item.objects.filter(
            tipo='produto',
            quantidade_estoque__lte=models.F('estoque_minimo')
        ).count()
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'servicos/item_detail.html'


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    template_name = 'servicos/item_form.html'
    fields = ['tipo', 'nome', 'preco', 'descricao', 'quantidade_estoque', 'estoque_minimo']
    success_url = reverse_lazy('servicos:item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Item cadastrado com sucesso!')
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    template_name = 'servicos/item_form.html'
    fields = ['tipo', 'nome', 'preco', 'descricao', 'quantidade_estoque', 'estoque_minimo', 'ativo']
    success_url = reverse_lazy('servicos:item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Item atualizado com sucesso!')
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = 'servicos/confirm_delete.html'
    success_url = reverse_lazy('servicos:item_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Item excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def buscar_itens(request):
    """API para busca de itens (serviços e produtos)."""
    termo = request.GET.get('q', '')
    tipo = request.GET.get('tipo', '')
    
    queryset = Item.objects.filter(ativo=True)
    
    if termo:
        queryset = queryset.filter(
            Q(nome__icontains=termo) |
            Q(id__icontains=termo if termo.isdigit() else -1)
        )
    
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    itens = queryset[:20]
    
    resultados = []
    for item in itens:
        tipo_display = 'Serviço' if item.tipo == 'servico' else 'Produto'
        resultados.append({
            'id': item.id,
            'nome': item.nome,
            'tipo': item.tipo,
            'preco': float(item.preco),
            'quantidade_estoque': item.quantidade_estoque,
            'texto': f"[{tipo_display}] {item.nome} - R$ {item.preco:.2f}"
        })
    
    return JsonResponse({'resultados': resultados})


@login_required
def obter_preco_item(request, pk):
    """API para obter o preço de um item."""
    item = get_object_or_404(Item, pk=pk)
    return JsonResponse({
        'id': item.id,
        'nome': item.nome,
        'preco': float(item.preco),
        'tipo': item.tipo,
        'quantidade_estoque': item.quantidade_estoque
    })


from django.db import models
