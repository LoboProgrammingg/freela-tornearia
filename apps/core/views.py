from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal

from .models import ConfiguracaoEmpresa
from apps.financeiro.models import Venda, Despesa, Parcela
from apps.cadastros.models import Funcionario


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal com métricas do negócio."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        hoje = timezone.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        periodo = self.request.GET.get('periodo', 'mes')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        
        if data_inicio and data_fim:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            except ValueError:
                data_inicio = primeiro_dia_mes
                data_fim = hoje
        else:
            if periodo == 'dia':
                data_inicio = hoje
                data_fim = hoje
            elif periodo == 'semana':
                data_inicio = hoje - timedelta(days=hoje.weekday())
                data_fim = hoje
            elif periodo == 'ano':
                data_inicio = hoje.replace(month=1, day=1)
                data_fim = hoje
            else:
                data_inicio = primeiro_dia_mes
                data_fim = hoje
        
        vendas_periodo = Venda.objects.filter(
            status='concluido',
            data_conclusao__gte=data_inicio,
            data_conclusao__lte=data_fim
        )
        
        # Total de receitas = todas as vendas registradas no período (à vista + parcelado)
        vendas_registradas = Venda.objects.filter(
            data_entrada__gte=data_inicio,
            data_entrada__lte=data_fim
        ).exclude(status='cancelado')
        total_receitas = sum(v.total for v in vendas_registradas) or Decimal('0')
        
        despesas_periodo = Despesa.objects.filter(
            data__gte=data_inicio,
            data__lte=data_fim
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        funcionarios_ativos = Funcionario.objects.filter(status='ativo')
        total_salarios = funcionarios_ativos.aggregate(total=Sum('salario'))['total'] or Decimal('0')
        
        total_despesas = despesas_periodo + total_salarios
        lucro_liquido = total_receitas - total_despesas
        
        servicos_andamento = Venda.objects.filter(status='em_andamento').count()
        servicos_concluidos = vendas_periodo.count()
        
        # Vendas concluídas = todas pagas (automaticamente)
        vendas_concluidas = Venda.objects.filter(status='concluido')
        
        # Vendas em andamento com parcelas pendentes
        vendas_em_andamento = Venda.objects.filter(status='em_andamento')
        vendas_com_pagamento_pendente = [v for v in vendas_em_andamento if v.parcelas.filter(pago=False).exists()]
        
        # Total recebido = todas as parcelas pagas (do mês atual)
        parcelas_pagas_periodo = Parcela.objects.filter(
            pago=True,
            data_pagamento__gte=data_inicio,
            data_pagamento__lte=data_fim
        )
        total_recebido = sum(p.valor for p in parcelas_pagas_periodo)
        
        # Total pendente = parcelas não pagas de vendas em andamento
        parcelas_pendentes = Parcela.objects.filter(
            pago=False,
            venda__status='em_andamento'
        )
        total_pendente = sum(p.valor for p in parcelas_pendentes)
        
        # Parcelas vencidas = pendentes com data passada
        parcelas_vencidas = Parcela.objects.filter(
            pago=False, 
            data_vencimento__lt=hoje,
            venda__status='em_andamento'
        )
        total_vencido = sum(p.valor for p in parcelas_vencidas)

        # Paginação de serviços em andamento
        vendas_andamento_list = Venda.objects.filter(status='em_andamento').order_by('-data_entrada')
        paginator_vendas = Paginator(vendas_andamento_list, 5)
        page_vendas = self.request.GET.get('page_vendas', 1)
        vendas_recentes = paginator_vendas.get_page(page_vendas)
        
        # Paginação de parcelas vencidas
        parcelas_vencidas_list = parcelas_vencidas.order_by('data_vencimento')
        paginator_parcelas = Paginator(parcelas_vencidas_list, 5)
        page_parcelas = self.request.GET.get('page_parcelas', 1)
        parcelas_vencidas_pag = paginator_parcelas.get_page(page_parcelas)

        context.update({
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'lucro_liquido': lucro_liquido,
            'servicos_andamento': servicos_andamento,
            'servicos_concluidos': servicos_concluidos,
            'periodo': periodo,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'vendas_recentes': vendas_recentes,
            'total_recebido': total_recebido,
            'total_pendente': total_pendente,
            'total_vencido': total_vencido,
            'vendas_pagamento_pendente': len(vendas_com_pagamento_pendente),
            'parcelas_vencidas': parcelas_vencidas_pag,
            'total_parcelas_vencidas': parcelas_vencidas_list.count(),
        })
        
        return context


class ConfiguracaoEmpresaView(LoginRequiredMixin, UpdateView):
    """View para configurações da empresa."""
    model = ConfiguracaoEmpresa
    template_name = 'core/configuracao.html'
    fields = ['nome', 'cnpj', 'endereco', 'telefone', 'email', 'logo', 'observacoes_padrao']
    success_url = '/configuracao/'

    def get_object(self, queryset=None):
        obj, created = ConfiguracaoEmpresa.objects.get_or_create(
            pk=1,
            defaults={'nome': 'Tornearia Jair'}
        )
        return obj


@login_required
def dashboard_data_api(request):
    """API para dados do dashboard (gráficos)."""
    hoje = timezone.now().date()
    periodo = request.GET.get('periodo', 'mes')
    
    if periodo == 'ano':
        meses = []
        for i in range(12, 0, -1):
            data = hoje.replace(day=1) - timedelta(days=30*i)
            meses.append(data.replace(day=1))
        
        receitas_mes = []
        despesas_mes = []
        labels = []
        
        for mes in meses:
            proximo_mes = (mes + timedelta(days=32)).replace(day=1)
            
            vendas = Venda.objects.filter(
                status='concluido',
                data_conclusao__gte=mes,
                data_conclusao__lt=proximo_mes
            )
            receita = sum(v.total for v in vendas)
            
            despesa = Despesa.objects.filter(
                data__gte=mes,
                data__lt=proximo_mes
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            receitas_mes.append(float(receita))
            despesas_mes.append(float(despesa))
            labels.append(mes.strftime('%b/%Y'))
    else:
        primeiro_dia_mes = hoje.replace(day=1)
        vendas = Venda.objects.filter(
            status='concluido',
            data_conclusao__gte=primeiro_dia_mes
        ).annotate(dia=TruncDay('data_conclusao')).values('dia').annotate(
            total=Count('id')
        ).order_by('dia')
        
        receitas_mes = []
        labels = []
        for v in vendas:
            labels.append(v['dia'].strftime('%d/%m'))
            
        despesas_mes = []

    top_servicos = []
    vendas_concluidas = Venda.objects.filter(status='concluido')
    
    from apps.financeiro.models import ItemVenda
    from apps.servicos.models import Item
    
    itens_vendidos = ItemVenda.objects.filter(
        venda__status='concluido'
    ).values('item__nome').annotate(
        total_vendido=Sum('quantidade'),
        receita_total=Sum('valor_unitario')
    ).order_by('-receita_total')[:5]
    
    for item in itens_vendidos:
        top_servicos.append({
            'nome': item['item__nome'],
            'receita': float(item['receita_total'] or 0)
        })

    categorias_despesas = Despesa.objects.values('categoria__nome').annotate(
        total=Sum('valor')
    ).order_by('-total')[:5]
    
    despesas_por_categoria = [
        {'categoria': d['categoria__nome'] or 'Sem categoria', 'total': float(d['total'])}
        for d in categorias_despesas
    ]

    return JsonResponse({
        'labels': labels,
        'receitas': receitas_mes,
        'despesas': despesas_mes,
        'top_servicos': top_servicos,
        'despesas_por_categoria': despesas_por_categoria,
    })
