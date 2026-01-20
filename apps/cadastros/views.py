from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .models import Empresa, Cliente, Funcionario


class EmpresaListView(LoginRequiredMixin, ListView):
    model = Empresa
    template_name = 'cadastros/empresa_list.html'
    context_object_name = 'empresas'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(cnpj__icontains=busca) |
                Q(nome_contato__icontains=busca)
            )
        return queryset


class EmpresaDetailView(LoginRequiredMixin, DetailView):
    model = Empresa
    template_name = 'cadastros/empresa_detail.html'


class EmpresaCreateView(LoginRequiredMixin, CreateView):
    model = Empresa
    template_name = 'cadastros/empresa_form.html'
    fields = ['nome', 'cnpj', 'nome_contato', 'telefone', 'email', 'endereco', 'observacoes']
    success_url = reverse_lazy('cadastros:empresa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa cadastrada com sucesso!')
        return super().form_valid(form)


class EmpresaUpdateView(LoginRequiredMixin, UpdateView):
    model = Empresa
    template_name = 'cadastros/empresa_form.html'
    fields = ['nome', 'cnpj', 'nome_contato', 'telefone', 'email', 'endereco', 'observacoes', 'ativo']
    success_url = reverse_lazy('cadastros:empresa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa atualizada com sucesso!')
        return super().form_valid(form)


class EmpresaDeleteView(LoginRequiredMixin, DeleteView):
    model = Empresa
    template_name = 'cadastros/confirm_delete.html'
    success_url = reverse_lazy('cadastros:empresa_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Empresa excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'cadastros/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(cpf__icontains=busca) |
                Q(telefone__icontains=busca)
            )
        return queryset


class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'cadastros/cliente_detail.html'


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'cadastros/cliente_form.html'
    fields = ['nome', 'cpf', 'telefone', 'email', 'endereco', 'observacoes']
    success_url = reverse_lazy('cadastros:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'cadastros/cliente_form.html'
    fields = ['nome', 'cpf', 'telefone', 'email', 'endereco', 'observacoes', 'ativo']
    success_url = reverse_lazy('cadastros:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'cadastros/confirm_delete.html'
    success_url = reverse_lazy('cadastros:cliente_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cliente excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class FuncionarioListView(LoginRequiredMixin, ListView):
    model = Funcionario
    template_name = 'cadastros/funcionario_list.html'
    context_object_name = 'funcionarios'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(cargo__icontains=busca)
            )
        return queryset


class FuncionarioDetailView(LoginRequiredMixin, DetailView):
    model = Funcionario
    template_name = 'cadastros/funcionario_detail.html'


class FuncionarioCreateView(LoginRequiredMixin, CreateView):
    model = Funcionario
    template_name = 'cadastros/funcionario_form.html'
    fields = ['nome', 'cargo', 'salario', 'data_admissao', 'telefone', 'observacoes']
    success_url = reverse_lazy('cadastros:funcionario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Funcionário cadastrado com sucesso!')
        return super().form_valid(form)


class FuncionarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Funcionario
    template_name = 'cadastros/funcionario_form.html'
    fields = ['nome', 'cargo', 'salario', 'data_admissao', 'telefone', 'observacoes', 'status']
    success_url = reverse_lazy('cadastros:funcionario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Funcionário atualizado com sucesso!')
        return super().form_valid(form)


class FuncionarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Funcionario
    template_name = 'cadastros/confirm_delete.html'
    success_url = reverse_lazy('cadastros:funcionario_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Funcionário excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def buscar_cliente_empresa(request):
    """API para busca de clientes e empresas."""
    termo = request.GET.get('q', '')
    tipo = request.GET.get('tipo', 'todos')
    
    resultados = []
    
    if tipo in ['todos', 'cliente']:
        clientes = Cliente.objects.filter(
            Q(nome__icontains=termo) |
            Q(cpf__icontains=termo) |
            Q(id__icontains=termo if termo.isdigit() else -1),
            ativo=True
        )[:10]
        
        for cliente in clientes:
            resultados.append({
                'id': cliente.id,
                'tipo': 'cliente',
                'nome': cliente.nome,
                'documento': cliente.cpf or '',
                'texto': f"[Cliente] {cliente.nome}" + (f" ({cliente.cpf})" if cliente.cpf else "")
            })
    
    if tipo in ['todos', 'empresa']:
        empresas = Empresa.objects.filter(
            Q(nome__icontains=termo) |
            Q(cnpj__icontains=termo) |
            Q(id__icontains=termo if termo.isdigit() else -1),
            ativo=True
        )[:10]
        
        for empresa in empresas:
            resultados.append({
                'id': empresa.id,
                'tipo': 'empresa',
                'nome': empresa.nome,
                'documento': empresa.cnpj or '',
                'texto': f"[Empresa] {empresa.nome}" + (f" ({empresa.cnpj})" if empresa.cnpj else "")
            })
    
    return JsonResponse({'resultados': resultados})
