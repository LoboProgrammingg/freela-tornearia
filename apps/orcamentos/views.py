from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from .models import Orcamento, ItemOrcamento
from apps.cadastros.models import Cliente, Empresa
from apps.servicos.models import Item
from apps.financeiro.models import Venda, ItemVenda
from apps.core.models import ConfiguracaoEmpresa

from io import BytesIO


class OrcamentoListView(LoginRequiredMixin, ListView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_list.html'
    context_object_name = 'orcamentos'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        status = self.request.GET.get('status')
        
        if busca:
            queryset = queryset.filter(
                Q(numero__icontains=busca) |
                Q(cliente__nome__icontains=busca) |
                Q(empresa__nome__icontains=busca)
            )
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filtro'] = self.request.GET.get('status', '')
        return context


class OrcamentoDetailView(LoginRequiredMixin, DetailView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_detail.html'


class OrcamentoCreateView(LoginRequiredMixin, CreateView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_form.html'
    fields = ['cliente', 'empresa', 'validade', 'desconto', 'observacoes', 'condicoes_pagamento']

    def get_initial(self):
        initial = super().get_initial()
        initial['validade'] = timezone.now().date() + timedelta(days=30)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.filter(ativo=True)
        context['empresas'] = Empresa.objects.filter(ativo=True)
        context['itens'] = Item.objects.filter(ativo=True)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        itens_ids = self.request.POST.getlist('item_id[]')
        quantidades = self.request.POST.getlist('quantidade[]')
        valores = self.request.POST.getlist('valor_unitario[]')
        descricoes = self.request.POST.getlist('descricao_adicional[]')
        
        for i, item_id in enumerate(itens_ids):
            if item_id:
                ItemOrcamento.objects.create(
                    orcamento=self.object,
                    item_id=int(item_id),
                    quantidade=int(quantidades[i]) if quantidades[i] else 1,
                    valor_unitario=float(valores[i]) if valores[i] else Item.objects.get(id=item_id).preco,
                    descricao_adicional=descricoes[i] if i < len(descricoes) else ''
                )
        
        messages.success(self.request, f'Orçamento {self.object.numero} criado com sucesso!')
        return response

    def get_success_url(self):
        return reverse('orcamentos:orcamento_detail', kwargs={'pk': self.object.pk})


class OrcamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_form.html'
    fields = ['cliente', 'empresa', 'validade', 'desconto', 'observacoes', 'condicoes_pagamento']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.filter(ativo=True)
        context['empresas'] = Empresa.objects.filter(ativo=True)
        context['itens'] = Item.objects.filter(ativo=True)
        context['itens_orcamento'] = self.object.itens.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        self.object.itens.all().delete()
        
        itens_ids = self.request.POST.getlist('item_id[]')
        quantidades = self.request.POST.getlist('quantidade[]')
        valores = self.request.POST.getlist('valor_unitario[]')
        descricoes = self.request.POST.getlist('descricao_adicional[]')
        
        for i, item_id in enumerate(itens_ids):
            if item_id:
                ItemOrcamento.objects.create(
                    orcamento=self.object,
                    item_id=int(item_id),
                    quantidade=int(quantidades[i]) if quantidades[i] else 1,
                    valor_unitario=float(valores[i]) if valores[i] else Item.objects.get(id=item_id).preco,
                    descricao_adicional=descricoes[i] if i < len(descricoes) else ''
                )
        
        messages.success(self.request, f'Orçamento {self.object.numero} atualizado com sucesso!')
        return response

    def get_success_url(self):
        return reverse('orcamentos:orcamento_detail', kwargs={'pk': self.object.pk})


class OrcamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Orcamento
    template_name = 'orcamentos/confirm_delete.html'
    success_url = reverse_lazy('orcamentos:orcamento_list')

    def delete(self, request, *args, **kwargs):
        orcamento = self.get_object()
        messages.success(request, f'Orçamento {orcamento.numero} excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def aprovar_orcamento(request, pk):
    """Aprova um orçamento."""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    if orcamento.status == 'pendente':
        orcamento.status = 'aprovado'
        orcamento.save()
        messages.success(request, f'Orçamento {orcamento.numero} aprovado com sucesso!')
    else:
        messages.warning(request, 'Este orçamento não pode ser aprovado.')
    return redirect('orcamentos:orcamento_detail', pk=pk)


@login_required
def rejeitar_orcamento(request, pk):
    """Rejeita um orçamento."""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    if orcamento.status == 'pendente':
        orcamento.status = 'rejeitado'
        orcamento.save()
        messages.success(request, f'Orçamento {orcamento.numero} rejeitado.')
    else:
        messages.warning(request, 'Este orçamento não pode ser rejeitado.')
    return redirect('orcamentos:orcamento_detail', pk=pk)


@login_required
def converter_orcamento_venda(request, pk):
    """Converte um orçamento aprovado em venda."""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if orcamento.status != 'aprovado':
        messages.warning(request, 'Apenas orçamentos aprovados podem ser convertidos em venda.')
        return redirect('orcamentos:orcamento_detail', pk=pk)
    
    venda = Venda.objects.create(
        orcamento=orcamento,
        cliente=orcamento.cliente,
        empresa=orcamento.empresa,
        data_entrada=timezone.now().date(),
        desconto=orcamento.desconto,
        observacoes=f"Convertido do orçamento {orcamento.numero}\n{orcamento.observacoes}"
    )
    
    for item_orc in orcamento.itens.all():
        ItemVenda.objects.create(
            venda=venda,
            item=item_orc.item,
            quantidade=item_orc.quantidade,
            valor_unitario=item_orc.valor_unitario,
            descricao_adicional=item_orc.descricao_adicional
        )
    
    orcamento.status = 'convertido'
    orcamento.save()
    
    messages.success(request, f'Orçamento convertido em venda {venda.numero} com sucesso!')
    return redirect('financeiro:venda_detail', pk=venda.pk)


@login_required
def gerar_pdf_orcamento(request, pk):
    """Gera PDF do orçamento."""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    try:
        config = ConfiguracaoEmpresa.objects.get(pk=1)
        empresa_nome = config.nome
        empresa_info = f"{config.endereco}\nTel: {config.telefone}\nEmail: {config.email}"
        if config.cnpj:
            empresa_info += f"\nCNPJ: {config.cnpj}"
    except ConfiguracaoEmpresa.DoesNotExist:
        empresa_nome = "Tornearia Jair"
        empresa_info = ""
    
    elements.append(Paragraph(empresa_nome, titulo_style))
    if empresa_info:
        elements.append(Paragraph(empresa_info.replace('\n', '<br/>'), normal_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph(f"<b>ORÇAMENTO {orcamento.numero}</b>", titulo_style))
    elements.append(Spacer(1, 10))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=10)
    
    destinatario = orcamento.empresa or orcamento.cliente
    elements.append(Paragraph(f"<b>Cliente:</b> {destinatario.nome if destinatario else 'Não informado'}", info_style))
    
    if orcamento.empresa and orcamento.empresa.cnpj:
        elements.append(Paragraph(f"<b>CNPJ:</b> {orcamento.empresa.cnpj}", info_style))
    elif orcamento.cliente and orcamento.cliente.cpf:
        elements.append(Paragraph(f"<b>CPF:</b> {orcamento.cliente.cpf}", info_style))
    
    elements.append(Paragraph(f"<b>Data de Emissão:</b> {orcamento.data_emissao.strftime('%d/%m/%Y')}", info_style))
    elements.append(Paragraph(f"<b>Validade:</b> {orcamento.validade.strftime('%d/%m/%Y')}", info_style))
    elements.append(Spacer(1, 20))
    
    data = [['Item', 'Descrição', 'Qtd', 'Valor Unit.', 'Total']]
    for item in orcamento.itens.all():
        data.append([
            item.item.nome,
            item.descricao_adicional or item.item.descricao or '-',
            str(item.quantidade),
            f"R$ {item.valor_unitario:.2f}",
            f"R$ {item.total:.2f}"
        ])
    
    table = Table(data, colWidths=[4*cm, 6*cm, 1.5*cm, 2.5*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    totais_style = ParagraphStyle('TotaisStyle', parent=styles['Normal'], fontSize=11, alignment=TA_RIGHT)
    elements.append(Paragraph(f"<b>Subtotal:</b> R$ {orcamento.subtotal:.2f}", totais_style))
    if orcamento.desconto > 0:
        elements.append(Paragraph(f"<b>Desconto ({orcamento.desconto}%):</b> - R$ {orcamento.valor_desconto:.2f}", totais_style))
    elements.append(Paragraph(f"<b>TOTAL:</b> R$ {orcamento.total:.2f}", totais_style))
    elements.append(Spacer(1, 30))
    
    if orcamento.condicoes_pagamento:
        elements.append(Paragraph("<b>Condições de Pagamento:</b>", info_style))
        elements.append(Paragraph(orcamento.condicoes_pagamento, normal_style))
        elements.append(Spacer(1, 10))
    
    if orcamento.observacoes:
        elements.append(Paragraph("<b>Observações:</b>", info_style))
        elements.append(Paragraph(orcamento.observacoes, normal_style))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orcamento_{orcamento.numero}.pdf"'
    return response
