from django.contrib import admin
from .models import Venda, ItemVenda, CategoriaDespesa, Despesa


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1
    autocomplete_fields = ['item']


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'destinatario_nome', 'status', 'data_entrada', 'data_conclusao', 'total')
    list_filter = ('status', 'data_entrada', 'forma_pagamento')
    search_fields = ('numero', 'cliente__nome', 'empresa__nome')
    autocomplete_fields = ['cliente', 'empresa', 'orcamento']
    inlines = [ItemVendaInline]
    readonly_fields = ('numero',)


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor')
    search_fields = ('nome',)


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'valor', 'data', 'tipo')
    list_filter = ('categoria', 'tipo', 'data')
    search_fields = ('descricao',)
    date_hierarchy = 'data'
