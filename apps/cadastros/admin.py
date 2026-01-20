from django.contrib import admin
from .models import Empresa, Cliente, Funcionario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'nome_contato', 'telefone', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'cnpj', 'nome_contato')
    list_editable = ('ativo',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'email', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'cpf', 'telefone')
    list_editable = ('ativo',)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'salario', 'status', 'data_admissao')
    list_filter = ('status', 'cargo')
    search_fields = ('nome', 'cargo')
    list_editable = ('status',)
