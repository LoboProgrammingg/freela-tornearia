from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Item(models.Model):
    """Model unificado para serviços e produtos em estoque."""
    TIPO_CHOICES = [
        ('servico', 'Serviço'),
        ('produto', 'Produto'),
    ]

    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    nome = models.CharField('Nome', max_length=200)
    preco = models.DecimalField(
        'Preço',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    descricao = models.TextField('Descrição', blank=True)
    quantidade_estoque = models.PositiveIntegerField(
        'Quantidade em Estoque',
        default=0,
        help_text='Obrigatório apenas para produtos'
    )
    estoque_minimo = models.PositiveIntegerField(
        'Estoque Mínimo',
        default=0,
        help_text='Quantidade mínima para alerta'
    )
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['tipo', 'nome']

    def __str__(self):
        tipo_display = 'Serviço' if self.tipo == 'servico' else 'Produto'
        return f"[{tipo_display}] {self.nome}"

    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo."""
        if self.tipo == 'produto':
            return self.quantidade_estoque <= self.estoque_minimo
        return False

    def atualizar_estoque(self, quantidade, operacao='saida'):
        """Atualiza o estoque do produto."""
        if self.tipo != 'produto':
            return
        
        if operacao == 'saida':
            self.quantidade_estoque = max(0, self.quantidade_estoque - quantidade)
        else:
            self.quantidade_estoque += quantidade
        self.save()
