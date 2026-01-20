from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.cadastros.models import Cliente, Empresa
from apps.servicos.models import Item


class Orcamento(models.Model):
    """Model para orçamentos."""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('convertido', 'Convertido em Venda'),
    ]

    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cliente',
        related_name='orcamentos'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa',
        related_name='orcamentos'
    )
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='pendente')
    data_emissao = models.DateField('Data de Emissão', auto_now_add=True)
    validade = models.DateField('Validade')
    desconto = models.DecimalField(
        'Desconto (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    observacoes = models.TextField('Observações', blank=True)
    condicoes_pagamento = models.TextField('Condições de Pagamento', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-created_at']

    def __str__(self):
        destinatario = self.empresa or self.cliente
        return f"Orçamento {self.numero} - {destinatario}"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = Orcamento.objects.order_by('-id').first()
            if ultimo:
                ultimo_numero = int(ultimo.numero.replace('ORC', ''))
                self.numero = f"ORC{ultimo_numero + 1:05d}"
            else:
                self.numero = "ORC00001"
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
        """Calcula o total do orçamento."""
        return self.subtotal - self.valor_desconto

    @property
    def destinatario_nome(self):
        """Retorna o nome do destinatário (cliente ou empresa)."""
        if self.empresa:
            return self.empresa.nome
        if self.cliente:
            return self.cliente.nome
        return "Não informado"


class ItemOrcamento(models.Model):
    """Model para itens de um orçamento."""
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        verbose_name='Orçamento',
        related_name='itens'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name='Item',
        related_name='itens_orcamento'
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
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'

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
