from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.cadastros.models import Cliente, Empresa, Funcionario
from apps.servicos.models import Item
from apps.orcamentos.models import Orcamento


class Venda(models.Model):
    """Model para registro de vendas/serviços executados."""
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao_debito', 'Cartão de Débito'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('boleto', 'Boleto'),
        ('transferencia', 'Transferência'),
        ('cheque', 'Cheque'),
    ]

    TIPO_PAGAMENTO_CHOICES = [
        ('a_vista', 'À Vista'),
        ('parcelado', 'Parcelado'),
    ]

    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    orcamento = models.OneToOneField(
        Orcamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Orçamento Origem',
        related_name='venda'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cliente',
        related_name='vendas'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa',
        related_name='vendas'
    )
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='em_andamento')
    data_entrada = models.DateField('Data de Entrada')
    data_conclusao = models.DateField('Data de Conclusão', null=True, blank=True)
    desconto = models.DecimalField(
        'Desconto (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    forma_pagamento = models.CharField(
        'Forma de Pagamento',
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True
    )
    tipo_pagamento = models.CharField(
        'Tipo de Pagamento',
        max_length=15,
        choices=TIPO_PAGAMENTO_CHOICES,
        default='a_vista'
    )
    numero_parcelas = models.PositiveIntegerField('Número de Parcelas', default=1)
    observacoes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Venda/Serviço'
        verbose_name_plural = 'Vendas/Serviços'
        ordering = ['-created_at']

    def __str__(self):
        destinatario = self.empresa or self.cliente
        return f"Venda {self.numero} - {destinatario}"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = Venda.objects.order_by('-id').first()
            if ultimo:
                ultimo_numero = int(ultimo.numero.replace('VND', ''))
                self.numero = f"VND{ultimo_numero + 1:05d}"
            else:
                self.numero = "VND00001"
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calcula o subtotal dos itens."""
        return sum(item.total for item in self.itens.all())

    @property
    def valor_desconto(self):
        """Calcula o valor do desconto."""
        return self.subtotal * (self.desconto / 100)

    @property
    def total(self):
        """Calcula o total da venda."""
        return self.subtotal - self.valor_desconto

    @property
    def destinatario_nome(self):
        """Retorna o nome do destinatário."""
        if self.empresa:
            return self.empresa.nome
        if self.cliente:
            return self.cliente.nome
        return "Não informado"

    def concluir(self):
        """Conclui a venda, atualiza estoque e marca todas as parcelas como pagas."""
        self.status = 'concluido'
        self.data_conclusao = timezone.localdate()
        for item_venda in self.itens.all():
            if item_venda.item.tipo == 'produto':
                item_venda.item.atualizar_estoque(item_venda.quantidade, 'saida')
        self.save()
        
        # Marcar todas as parcelas como pagas automaticamente
        for parcela in self.parcelas.filter(pago=False):
            parcela.pago = True
            parcela.data_pagamento = timezone.localdate()
            parcela.save()

    def gerar_parcelas(self):
        """Gera as parcelas da venda se for parcelado."""
        if self.tipo_pagamento == 'parcelado' and self.numero_parcelas > 1:
            self.parcelas.all().delete()
            valor_parcela = self.total / self.numero_parcelas
            for i in range(1, self.numero_parcelas + 1):
                from dateutil.relativedelta import relativedelta
                data_vencimento = self.data_entrada + relativedelta(months=i-1)
                Parcela.objects.create(
                    venda=self,
                    numero=i,
                    valor=valor_parcela,
                    data_vencimento=data_vencimento
                )
        elif self.tipo_pagamento == 'a_vista':
            self.parcelas.all().delete()
            Parcela.objects.create(
                venda=self,
                numero=1,
                valor=self.total,
                data_vencimento=self.data_entrada,
                pago=False
            )

    @property
    def valor_recebido(self):
        """Retorna o valor total já recebido."""
        return sum(p.valor for p in self.parcelas.filter(pago=True))

    @property
    def valor_pendente(self):
        """Retorna o valor ainda pendente de recebimento."""
        return self.total - self.valor_recebido

    @property
    def parcelas_pagas(self):
        """Retorna quantidade de parcelas pagas."""
        return self.parcelas.filter(pago=True).count()

    @property
    def pagamento_completo(self):
        """Verifica se o pagamento está completo."""
        return self.parcelas.filter(pago=False).count() == 0 and self.parcelas.exists()


class ItemVenda(models.Model):
    """Model para itens de uma venda."""
    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        verbose_name='Venda',
        related_name='itens'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name='Item',
        related_name='itens_venda'
    )
    quantidade = models.PositiveIntegerField('Quantidade', default=1)
    valor_unitario = models.DecimalField(
        'Valor Unitário',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    descricao_adicional = models.CharField('Descrição Adicional', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'

    def __str__(self):
        return f"{self.item.nome} x {self.quantidade}"

    @property
    def total(self):
        """Calcula o total do item."""
        return self.quantidade * self.valor_unitario

    def save(self, *args, **kwargs):
        if not self.valor_unitario:
            self.valor_unitario = self.item.preco
        super().save(*args, **kwargs)


class CategoriaDespesa(models.Model):
    """Model para categorias de despesas."""
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    cor = models.CharField('Cor (hex)', max_length=7, default='#6B7280')

    class Meta:
        verbose_name = 'Categoria de Despesa'
        verbose_name_plural = 'Categorias de Despesas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Parcela(models.Model):
    """Model para controle de parcelas de pagamento."""
    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        verbose_name='Venda',
        related_name='parcelas'
    )
    numero = models.PositiveIntegerField('Número da Parcela')
    valor = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    pago = models.BooleanField('Pago', default=False)
    observacoes = models.CharField('Observações', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['venda', 'numero']
        unique_together = ['venda', 'numero']

    def __str__(self):
        status = "✓" if self.pago else "○"
        return f"{status} Parcela {self.numero}/{self.venda.numero_parcelas} - R$ {self.valor}"

    def save(self, *args, **kwargs):
        """Override save para garantir data_pagamento quando pago."""
        if self.pago and not self.data_pagamento:
            self.data_pagamento = timezone.localdate()
        elif not self.pago:
            self.data_pagamento = None
        super().save(*args, **kwargs)

    def marcar_como_pago(self):
        """Marca a parcela como paga."""
        self.pago = True
        self.data_pagamento = timezone.localdate()
        self.save()

    @property
    def vencida(self):
        """Verifica se a parcela está vencida."""
        if self.pago:
            return False
        return self.data_vencimento < timezone.localdate()


class Despesa(models.Model):
    """Model para registro de despesas."""
    TIPO_CHOICES = [
        ('fixa', 'Fixa'),
        ('variavel', 'Variável'),
        ('salario', 'Salário'),
    ]

    descricao = models.CharField('Descrição', max_length=200)
    categoria = models.ForeignKey(
        CategoriaDespesa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Categoria',
        related_name='despesas'
    )
    valor = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    data = models.DateField('Data')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='variavel')
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Funcionário',
        related_name='pagamentos'
    )
    observacoes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-data']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"


class FolhaPagamento(models.Model):
    """Model para controle mensal de folha de pagamento."""
    mes = models.PositiveIntegerField('Mês')
    ano = models.PositiveIntegerField('Ano')
    data_geracao = models.DateTimeField('Data de Geração', auto_now_add=True)
    total = models.DecimalField(
        'Total',
        max_digits=12,
        decimal_places=2,
        default=0
    )
    processada = models.BooleanField('Processada', default=False)

    class Meta:
        verbose_name = 'Folha de Pagamento'
        verbose_name_plural = 'Folhas de Pagamento'
        ordering = ['-ano', '-mes']
        unique_together = ['mes', 'ano']

    def __str__(self):
        return f"Folha de Pagamento {self.mes:02d}/{self.ano}"

    @classmethod
    def gerar_folha(cls, mes, ano):
        """Gera ou atualiza a folha de pagamento do mês."""
        folha, created = cls.objects.get_or_create(mes=mes, ano=ano)
        
        if folha.processada:
            return folha, False, "Folha já foi processada"
        
        funcionarios_ativos = Funcionario.objects.filter(status='ativo')
        
        categoria_salario, _ = CategoriaDespesa.objects.get_or_create(
            nome='Salários',
            defaults={'cor': '#4CAF50', 'descricao': 'Pagamento de salários dos funcionários'}
        )
        
        total = Decimal('0')
        for func in funcionarios_ativos:
            despesa_existente = Despesa.objects.filter(
                funcionario=func,
                tipo='salario',
                data__month=mes,
                data__year=ano
            ).first()
            
            if not despesa_existente:
                from datetime import date
                Despesa.objects.create(
                    descricao=f"Salário {func.nome} - {mes:02d}/{ano}",
                    categoria=categoria_salario,
                    valor=func.salario,
                    data=date(ano, mes, 1),
                    tipo='salario',
                    funcionario=func
                )
            total += func.salario
        
        folha.total = total
        folha.save()
        
        return folha, True, f"Folha gerada com {funcionarios_ativos.count()} funcionário(s)"

    def processar(self):
        """Marca a folha como processada (paga)."""
        self.processada = True
        self.save()
