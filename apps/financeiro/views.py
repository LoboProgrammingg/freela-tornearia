from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from django.core.mail import EmailMessage
from django.conf import settings

from .models import Venda, ItemVenda, Despesa, CategoriaDespesa, Parcela, FolhaPagamento
from apps.cadastros.models import Cliente, Empresa, Funcionario
from apps.servicos.models import Item
from apps.core.models import ConfiguracaoEmpresa


class VendaListView(LoginRequiredMixin, ListView):
    model = Venda
    template_name = 'financeiro/venda_list.html'
    context_object_name = 'vendas'
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


class VendaDetailView(LoginRequiredMixin, DetailView):
    model = Venda
    template_name = 'financeiro/venda_detail.html'


class VendaCreateView(LoginRequiredMixin, CreateView):
    model = Venda
    template_name = 'financeiro/venda_form.html'
    fields = ['cliente', 'empresa', 'data_entrada', 'desconto', 'forma_pagamento', 'tipo_pagamento', 'numero_parcelas', 'observacoes']

    def get_initial(self):
        initial = super().get_initial()
        initial['data_entrada'] = timezone.localdate()
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
                ItemVenda.objects.create(
                    venda=self.object,
                    item_id=int(item_id),
                    quantidade=int(quantidades[i]) if quantidades[i] else 1,
                    valor_unitario=float(valores[i]) if valores[i] else Item.objects.get(id=item_id).preco,
                    descricao_adicional=descricoes[i] if i < len(descricoes) else ''
                )
        
        # Gerar parcelas automaticamente
        self.object.gerar_parcelas()
        
        messages.success(self.request, f'Serviço {self.object.numero} registrado com sucesso!')
        return response

    def get_success_url(self):
        return reverse('financeiro:venda_detail', kwargs={'pk': self.object.pk})


class VendaUpdateView(LoginRequiredMixin, UpdateView):
    model = Venda
    template_name = 'financeiro/venda_form.html'
    fields = ['cliente', 'empresa', 'data_entrada', 'desconto', 'forma_pagamento', 'tipo_pagamento', 'numero_parcelas', 'observacoes']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.filter(ativo=True)
        context['empresas'] = Empresa.objects.filter(ativo=True)
        context['itens'] = Item.objects.filter(ativo=True)
        context['itens_venda'] = self.object.itens.all()
        return context

    def form_valid(self, form):
        if self.object.status == 'concluido':
            messages.error(self.request, 'Não é possível editar uma venda concluída.')
            return redirect('financeiro:venda_detail', pk=self.object.pk)
        
        response = super().form_valid(form)
        
        self.object.itens.all().delete()
        
        itens_ids = self.request.POST.getlist('item_id[]')
        quantidades = self.request.POST.getlist('quantidade[]')
        valores = self.request.POST.getlist('valor_unitario[]')
        descricoes = self.request.POST.getlist('descricao_adicional[]')
        
        for i, item_id in enumerate(itens_ids):
            if item_id:
                ItemVenda.objects.create(
                    venda=self.object,
                    item_id=int(item_id),
                    quantidade=int(quantidades[i]) if quantidades[i] else 1,
                    valor_unitario=float(valores[i]) if valores[i] else Item.objects.get(id=item_id).preco,
                    descricao_adicional=descricoes[i] if i < len(descricoes) else ''
                )
        
        # Regenerar parcelas se mudou o tipo ou número
        self.object.gerar_parcelas()
        
        messages.success(self.request, f'Serviço {self.object.numero} atualizado com sucesso!')
        return response

    def get_success_url(self):
        return reverse('financeiro:venda_detail', kwargs={'pk': self.object.pk})


class VendaDeleteView(LoginRequiredMixin, DeleteView):
    model = Venda
    template_name = 'financeiro/confirm_delete.html'
    success_url = reverse_lazy('financeiro:venda_list')

    def delete(self, request, *args, **kwargs):
        venda = self.get_object()
        if venda.status == 'concluido':
            messages.error(request, 'Não é possível excluir uma venda concluída.')
            return redirect('financeiro:venda_detail', pk=venda.pk)
        messages.success(request, f'Venda {venda.numero} excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def concluir_venda(request, pk):
    """Conclui uma venda e atualiza o estoque."""
    venda = get_object_or_404(Venda, pk=pk)
    
    if venda.status == 'concluido':
        messages.warning(request, 'Esta venda já está concluída.')
        return redirect('financeiro:venda_detail', pk=pk)
    
    if venda.status == 'cancelado':
        messages.warning(request, 'Não é possível concluir uma venda cancelada.')
        return redirect('financeiro:venda_detail', pk=pk)
    
    venda.concluir()
    messages.success(request, f'Venda {venda.numero} concluída com sucesso! Estoque atualizado.')
    return redirect('financeiro:venda_detail', pk=pk)


@login_required
def cancelar_venda(request, pk):
    """Cancela uma venda."""
    venda = get_object_or_404(Venda, pk=pk)
    
    if venda.status == 'concluido':
        messages.warning(request, 'Não é possível cancelar uma venda concluída.')
        return redirect('financeiro:venda_detail', pk=pk)
    
    venda.status = 'cancelado'
    venda.save()
    messages.success(request, f'Venda {venda.numero} cancelada.')
    return redirect('financeiro:venda_detail', pk=pk)


@login_required
def marcar_parcela_paga(request, pk):
    """Marca uma parcela como paga."""
    parcela = get_object_or_404(Parcela, pk=pk)
    parcela.marcar_como_pago()
    messages.success(request, f'Parcela {parcela.numero} marcada como paga!')
    return redirect('financeiro:venda_detail', pk=parcela.venda.pk)


@login_required
def gerar_parcelas_venda(request, pk):
    """Gera ou regenera as parcelas de uma venda."""
    venda = get_object_or_404(Venda, pk=pk)
    venda.gerar_parcelas()
    messages.success(request, f'Parcelas geradas para a venda {venda.numero}!')
    return redirect('financeiro:venda_detail', pk=pk)


class FolhaPagamentoListView(LoginRequiredMixin, ListView):
    """Lista de folhas de pagamento."""
    model = FolhaPagamento
    template_name = 'financeiro/folha_list.html'
    context_object_name = 'folhas'
    
    def get_queryset(self):
        """Filtra folhas pelo mês/ano selecionado ou mês atual."""
        now = timezone.now()
        mes = int(self.request.GET.get('mes', now.month))
        ano = int(self.request.GET.get('ano', now.year))
        return FolhaPagamento.objects.filter(mes=mes, ano=ano).order_by('-data_geracao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['funcionarios_ativos'] = Funcionario.objects.filter(status='ativo')
        context['total_salarios'] = sum(f.salario for f in context['funcionarios_ativos'])
        
        # Informações do mês atual
        now = timezone.now()
        mes_selecionado = int(self.request.GET.get('mes', now.month))
        ano_selecionado = int(self.request.GET.get('ano', now.year))
        
        context['mes_atual'] = mes_selecionado
        context['ano_atual'] = ano_selecionado
        
        # Nome do mês em português
        meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        context['nome_mes_atual'] = meses[mes_selecionado]
        
        return context


@login_required
def gerar_folha_pagamento(request):
    """Gera a folha de pagamento do mês atual."""
    mes = int(request.GET.get('mes', timezone.now().month))
    ano = int(request.GET.get('ano', timezone.now().year))
    
    folha, sucesso, mensagem = FolhaPagamento.gerar_folha(mes, ano)
    
    if sucesso:
        messages.success(request, f'Folha de pagamento {mes:02d}/{ano} gerada! {mensagem}')
    else:
        messages.warning(request, mensagem)
    
    return redirect('financeiro:folha_list')


@login_required
def processar_folha_pagamento(request, pk):
    """Marca a folha de pagamento como processada."""
    folha = get_object_or_404(FolhaPagamento, pk=pk)
    
    if folha.processada:
        messages.warning(request, 'Esta folha já foi processada.')
    else:
        folha.processar()
        messages.success(request, f'Folha de pagamento {folha.mes:02d}/{folha.ano} marcada como processada!')
    
    return redirect('financeiro:folha_list')


class DespesaListView(LoginRequiredMixin, ListView):
    model = Despesa
    template_name = 'financeiro/despesa_list.html'
    context_object_name = 'despesas'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        categoria = self.request.GET.get('categoria')
        
        if busca:
            queryset = queryset.filter(
                Q(descricao__icontains=busca)
            )
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaDespesa.objects.all()
        context['categoria_filtro'] = self.request.GET.get('categoria', '')
        return context


class DespesaCreateView(LoginRequiredMixin, CreateView):
    model = Despesa
    template_name = 'financeiro/despesa_form.html'
    fields = ['descricao', 'categoria', 'valor', 'data', 'tipo', 'observacoes']
    success_url = reverse_lazy('financeiro:despesa_list')

    def get_initial(self):
        initial = super().get_initial()
        initial['data'] = timezone.localdate()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaDespesa.objects.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Despesa cadastrada com sucesso!')
        return super().form_valid(form)


class DespesaUpdateView(LoginRequiredMixin, UpdateView):
    model = Despesa
    template_name = 'financeiro/despesa_form.html'
    fields = ['descricao', 'categoria', 'valor', 'data', 'tipo', 'observacoes']
    success_url = reverse_lazy('financeiro:despesa_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaDespesa.objects.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Despesa atualizada com sucesso!')
        return super().form_valid(form)


class DespesaDeleteView(LoginRequiredMixin, DeleteView):
    model = Despesa
    template_name = 'financeiro/confirm_delete.html'
    success_url = reverse_lazy('financeiro:despesa_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Despesa excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class CategoriaListView(LoginRequiredMixin, ListView):
    model = CategoriaDespesa
    template_name = 'financeiro/categoria_list.html'
    context_object_name = 'categorias'


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaDespesa
    template_name = 'financeiro/categoria_form.html'
    fields = ['nome', 'descricao', 'cor']
    success_url = reverse_lazy('financeiro:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoria criada com sucesso!')
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaDespesa
    template_name = 'financeiro/categoria_form.html'
    fields = ['nome', 'descricao', 'cor']
    success_url = reverse_lazy('financeiro:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return super().form_valid(form)


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaDespesa
    template_name = 'financeiro/confirm_delete.html'
    success_url = reverse_lazy('financeiro:categoria_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoria excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def gerar_comprovante_venda(request, pk):
    """Gera um comprovante PDF elegante e profissional da venda/serviço."""
    import os
    from django.conf import settings
    
    venda = get_object_or_404(Venda, pk=pk)
    
    buffer = _gerar_pdf_bytes_venda(venda)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprovante_{venda.numero}.pdf"'
    return response


@login_required
def enviar_email_venda(request, pk):
    """Envia o comprovante da venda/serviço por e-mail com PDF anexo."""
    venda = get_object_or_404(Venda, pk=pk)
    
    destinatario_email = None
    destinatario_nome = "Cliente"
    
    if venda.empresa:
        destinatario_email = venda.empresa.email
        destinatario_nome = venda.empresa.nome
    elif venda.cliente:
        destinatario_email = venda.cliente.email
        destinatario_nome = venda.cliente.nome
        
    if not destinatario_email:
        messages.error(request, 'O cliente/empresa não possui e-mail cadastrado.')
        return redirect('financeiro:venda_detail', pk=pk)
        
    try:
        # Gerar PDF
        pdf_buffer = _gerar_pdf_bytes_venda(venda)
        pdf_content = pdf_buffer.getvalue()
        
        assunto = f"Comprovante de Venda/Serviço {venda.numero} - Tornearia Jair"
        mensagem = f'''Olá {destinatario_nome},
        
Segue em anexo o comprovante da Venda/Serviço {venda.numero}.

Atenciosamente,
Tornearia Jair
'''
        email = EmailMessage(
            subject=assunto,
            body=mensagem,
            from_email=settings.EMAIL_HOST_USER,
            to=[destinatario_email],
        )
        
        email.attach(f"comprovante_{venda.numero}.pdf", pdf_content, 'application/pdf')
        email.send()
        
        messages.success(request, f'E-mail enviado com sucesso para {destinatario_email}!')
        
    except Exception as e:
        messages.error(request, f'Erro ao enviar e-mail: {str(e)}')
        
    return redirect('financeiro:venda_detail', pk=pk)


def _gerar_pdf_bytes_venda(venda):
    """Função auxiliar para gerar o PDF da venda e retornar o buffer."""
    import os
    from django.conf import settings
    
    config = ConfiguracaoEmpresa.objects.first()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cores do tema
    COR_PRIMARIA = colors.HexColor('#1e3a5f')
    COR_SECUNDARIA = colors.HexColor('#2c5282')
    COR_ACCENT = colors.HexColor('#3182ce')
    COR_TEXTO = colors.HexColor('#2d3748')
    COR_TEXTO_CLARO = colors.HexColor('#718096')
    COR_FUNDO = colors.HexColor('#f7fafc')
    COR_BORDA = colors.HexColor('#e2e8f0')
    
    # Estilos customizados
    style_empresa_nome = ParagraphStyle(
        'EmpresaNome',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=COR_PRIMARIA,
        alignment=TA_LEFT,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    style_empresa_info = ParagraphStyle(
        'EmpresaInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COR_TEXTO_CLARO,
        alignment=TA_LEFT,
        leading=12
    )
    
    style_doc_tipo = ParagraphStyle(
        'DocTipo',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_doc_numero = ParagraphStyle(
        'DocNumero',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    style_secao_titulo = ParagraphStyle(
        'SecaoTitulo',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=COR_PRIMARIA,
        spaceBefore=12,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        leftIndent=0
    )
    
    style_label = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COR_TEXTO_CLARO,
        leading=10
    )
    
    style_valor = ParagraphStyle(
        'Valor',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COR_TEXTO,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    style_info = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COR_TEXTO,
        leading=12
    )
    
    style_total_label = ParagraphStyle(
        'TotalLabel',
        parent=styles['Normal'],
        fontSize=12,
        textColor=COR_TEXTO,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    style_total_valor = ParagraphStyle(
        'TotalValor',
        parent=styles['Normal'],
        fontSize=16,
        textColor=COR_PRIMARIA,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    style_rodape = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COR_TEXTO_CLARO,
        alignment=TA_CENTER,
        leading=11
    )
    
    style_agradecimento = ParagraphStyle(
        'Agradecimento',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COR_PRIMARIA,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # ===== CABEÇALHO COM LOGO E DADOS DA EMPRESA =====
    nome_empresa = config.nome if config else 'Tornearia Jair'
    
    # Dados da empresa
    empresa_info_lines = []
    if config:
        if config.cnpj:
            empresa_info_lines.append(f"<b>CNPJ:</b> {config.cnpj}")
        if config.endereco:
            empresa_info_lines.append(f"<b>Endereço:</b> {config.endereco}")
        if config.telefone:
            empresa_info_lines.append(f"<b>Telefone:</b> {config.telefone}")
        if config.email:
            empresa_info_lines.append(f"<b>E-mail:</b> {config.email}")
    
    empresa_info_text = "<br/>".join(empresa_info_lines) if empresa_info_lines else ""
    
    # Verificar se existe logo
    logo_element = None
    if config and config.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(config.logo))
        if os.path.exists(logo_path):
            try:
                logo_element = Image(logo_path, width=2.5*cm, height=2.5*cm)
                logo_element.hAlign = 'LEFT'
            except:
                logo_element = None
    
    # Construir cabeçalho
    if logo_element:
        header_data = [[
            logo_element,
            [Paragraph(nome_empresa.upper(), style_empresa_nome),
             Paragraph(empresa_info_text, style_empresa_info)]
        ]]
        header_table = Table(header_data, colWidths=[3*cm, 14.5*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        header_data = [[
            [Paragraph(nome_empresa.upper(), style_empresa_nome),
             Paragraph(empresa_info_text, style_empresa_info)]
        ]]
        header_table = Table(header_data, colWidths=[17.5*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # ===== FAIXA DO TIPO DE DOCUMENTO =====
    if venda.status == 'concluido':
        tipo_doc = "COMPROVANTE DE SERVIÇO"
    elif venda.status == 'em_andamento':
        tipo_doc = "ORDEM DE SERVIÇO"
    else:
        tipo_doc = "REGISTRO DE SERVIÇO"
    
    data_emissao = timezone.now().strftime('%d/%m/%Y às %H:%M')
    
    doc_header = Table(
        [[Paragraph(tipo_doc, style_doc_tipo)],
         [Paragraph(f"Nº {venda.numero} • Emitido em {data_emissao}", style_doc_numero)]],
        colWidths=[17.5*cm]
    )
    doc_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COR_PRIMARIA),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    elements.append(doc_header)
    elements.append(Spacer(1, 20))
    
    # ===== INFORMAÇÕES DO SERVIÇO E CLIENTE =====
    # Info cards lado a lado
    
    # Dados do cliente
    cliente_nome = venda.destinatario_nome
    cliente_doc = ""
    cliente_telefone = ""
    cliente_email = ""
    
    if venda.cliente:
        cliente_doc = venda.cliente.cpf or ""
        cliente_telefone = venda.cliente.telefone or ""
        cliente_email = venda.cliente.email or ""
    elif venda.empresa:
        cliente_doc = venda.empresa.cnpj or ""
        cliente_telefone = venda.empresa.telefone or ""
        cliente_email = venda.empresa.email or ""
    
    # Criar tabela com 2 colunas de informações
    info_data = []
    
    # Linha 1: Data de Entrada | Cliente
    info_data.append([
        Paragraph("<b>Data de Entrada:</b>", style_label),
        Paragraph(venda.data_entrada.strftime('%d/%m/%Y'), style_valor),
        Paragraph("<b>Cliente:</b>", style_label),
        Paragraph(cliente_nome, style_valor)
    ])
    
    # Linha 2: Status | Documento
    tipo_doc_cliente = "CPF" if venda.cliente else "CNPJ"
    info_data.append([
        Paragraph("<b>Status:</b>", style_label),
        Paragraph(venda.get_status_display(), style_valor),
        Paragraph(f"<b>{tipo_doc_cliente}:</b>", style_label),
        Paragraph(cliente_doc or "-", style_valor)
    ])
    
    # Linha 3: Forma de Pagamento | Telefone
    info_data.append([
        Paragraph("<b>Forma de Pagamento:</b>", style_label),
        Paragraph(venda.get_forma_pagamento_display() if venda.forma_pagamento else "-", style_valor),
        Paragraph("<b>Telefone:</b>", style_label),
        Paragraph(cliente_telefone or "-", style_valor)
    ])
    
    # Linha 4: Conclusão | Email (se houver)
    if venda.data_conclusao or cliente_email:
        info_data.append([
            Paragraph("<b>Data de Conclusão:</b>", style_label),
            Paragraph(venda.data_conclusao.strftime('%d/%m/%Y') if venda.data_conclusao else "-", style_valor),
            Paragraph("<b>E-mail:</b>", style_label),
            Paragraph(cliente_email or "-", style_valor)
        ])
    
    # Tabela de informações estruturada
    info_table = Table(info_data, colWidths=[3.5*cm, 5*cm, 3*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), COR_FUNDO),
        ('BOX', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, COR_BORDA),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, COR_BORDA),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # ===== TABELA DE ITENS =====
    elements.append(Paragraph("SERVIÇOS E PRODUTOS", style_secao_titulo))
    
    # Cabeçalho da tabela
    dados_itens = [
        [Paragraph("<b>#</b>", style_info),
         Paragraph("<b>DESCRIÇÃO</b>", style_info),
         Paragraph("<b>QTD</b>", style_info),
         Paragraph("<b>VALOR UNIT.</b>", style_info),
         Paragraph("<b>TOTAL</b>", style_info)]
    ]
    
    for idx, item in enumerate(venda.itens.all(), 1):
        tipo_badge = "[SERVIÇO]" if item.item.tipo == 'servico' else "[PRODUTO]"
        descricao = f"{item.item.nome}"
        if item.descricao_adicional:
            descricao += f" - {item.descricao_adicional}"
        
        dados_itens.append([
            Paragraph(str(idx), style_info),
            Paragraph(f"<font size='7' color='#718096'>{tipo_badge}</font> {descricao}", style_info),
            Paragraph(str(item.quantidade), style_info),
            Paragraph(f"R$ {item.valor_unitario:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), style_info),
            Paragraph(f"R$ {item.total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), style_info)
        ])
    
    tabela_itens = Table(dados_itens, colWidths=[1*cm, 9*cm, 1.5*cm, 3*cm, 3*cm])
    tabela_itens.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_SECUNDARIA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COR_FUNDO]),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tabela_itens)
    elements.append(Spacer(1, 15))
    
    # ===== RESUMO FINANCEIRO =====
    subtotal = venda.subtotal
    desconto_valor = venda.valor_desconto
    total = venda.total
    
    resumo_data = []
    resumo_data.append(['', '', Paragraph("Subtotal:", style_info), 
                        Paragraph(f"R$ {subtotal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), style_info)])
    
    if venda.desconto > 0:
        resumo_data.append(['', '', Paragraph(f"Desconto ({venda.desconto}%):", style_info),
                          Paragraph(f"- R$ {desconto_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
                                   ParagraphStyle('Desc', parent=style_info, textColor=colors.HexColor('#e53e3e')))])
    
    tabela_resumo = Table(resumo_data, colWidths=[8*cm, 3*cm, 3.5*cm, 3*cm])
    tabela_resumo.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(tabela_resumo)
    
    # Total em destaque
    elements.append(Spacer(1, 5))
    total_box = Table(
        [['', Paragraph("VALOR TOTAL", style_total_label),
          Paragraph(f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), style_total_valor)]],
        colWidths=[8*cm, 5*cm, 4.5*cm]
    )
    total_box.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (-1, 0), COR_FUNDO),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('TOPPADDING', (1, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (1, 0), (-1, 0), 12),
        ('LEFTPADDING', (1, 0), (-1, 0), 15),
        ('RIGHTPADDING', (1, 0), (-1, 0), 15),
        ('BOX', (1, 0), (-1, 0), 1.5, COR_PRIMARIA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(total_box)
    
    # ===== OBSERVAÇÕES =====
    if venda.observacoes:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("OBSERVAÇÕES", style_secao_titulo))
        obs_box = Table(
            [[Paragraph(venda.observacoes.replace('\n', '<br/>'), style_info)]],
            colWidths=[17.5*cm]
        )
        obs_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COR_FUNDO),
            ('BOX', (0, 0), (-1, -1), 0.5, COR_BORDA),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(obs_box)
    
    # ===== MENSAGEM DE AGRADECIMENTO =====
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Obrigado pela preferência!", style_agradecimento))
    
    # ===== RODAPÉ =====
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=10))
    
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
    
    rodape_texto = f"{nome_empresa}"
    if config:
        partes_rodape = []
        if config.endereco:
            partes_rodape.append(config.endereco)
        if config.telefone:
            partes_rodape.append(f"Tel: {config.telefone}")
        if config.email:
            partes_rodape.append(config.email)
        if partes_rodape:
            rodape_texto += "<br/>" + " • ".join(partes_rodape)
    
    elements.append(Paragraph(rodape_texto, style_rodape))
    
    # Gerar PDF
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Comprovante_{venda.numero}.pdf"'
    
    return response
