from django.contrib import admin
from .models import Orcamento, ItemOrcamento


class ItemOrcamentoInline(admin.TabularInline):
    model = ItemOrcamento
    extra = 1
    autocomplete_fields = ['item']


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'destinatario_nome', 'status', 'data_emissao', 'validade', 'total')
    list_filter = ('status', 'data_emissao')
    search_fields = ('numero', 'cliente__nome', 'empresa__nome')
    autocomplete_fields = ['cliente', 'empresa']
    inlines = [ItemOrcamentoInline]
    readonly_fields = ('numero',)
