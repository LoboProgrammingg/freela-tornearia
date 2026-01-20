from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'preco', 'quantidade_estoque', 'estoque_baixo', 'ativo')
    list_filter = ('tipo', 'ativo')
    search_fields = ('nome', 'descricao')
    list_editable = ('ativo', 'preco', 'quantidade_estoque')
    
    def estoque_baixo(self, obj):
        return obj.estoque_baixo
    estoque_baixo.boolean = True
    estoque_baixo.short_description = 'Estoque Baixo'
