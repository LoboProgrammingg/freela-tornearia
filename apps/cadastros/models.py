from django.db import models
from django.core.validators import RegexValidator


class Empresa(models.Model):
    """Model para cadastro de empresas (pessoa jurídica)."""
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message='CNPJ deve estar no formato: 00.000.000/0000-00'
            )
        ]
    )
    nome = models.CharField('Nome da Empresa', max_length=200)
    nome_contato = models.CharField('Nome do Contato', max_length=200, blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    endereco = models.TextField('Endereço', blank=True)
    observacoes = models.TextField('Observações', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        if self.cnpj:
            return f"{self.nome} ({self.cnpj})"
        return self.nome


class Cliente(models.Model):
    """Model para cadastro de clientes (pessoa física)."""
    cpf = models.CharField(
        'CPF',
        max_length=14,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF deve estar no formato: 000.000.000-00'
            )
        ]
    )
    nome = models.CharField('Nome', max_length=200)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    endereco = models.TextField('Endereço', blank=True)
    observacoes = models.TextField('Observações', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        if self.cpf:
            return f"{self.nome} ({self.cpf})"
        return self.nome


class Funcionario(models.Model):
    """Model para cadastro de funcionários."""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    nome = models.CharField('Nome', max_length=200)
    cargo = models.CharField('Cargo', max_length=100, blank=True)
    salario = models.DecimalField('Salário Mensal', max_digits=10, decimal_places=2)
    data_admissao = models.DateField('Data de Admissão', blank=True, null=True)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ativo')
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.cargo}" if self.cargo else self.nome
