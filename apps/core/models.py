from django.db import models


class ConfiguracaoEmpresa(models.Model):
    """Configurações da empresa para exibição em orçamentos e documentos."""
    nome = models.CharField('Nome da Empresa', max_length=200)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True)
    endereco = models.TextField('Endereço', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    logo = models.ImageField('Logo', upload_to='empresa/', blank=True, null=True)
    observacoes_padrao = models.TextField('Observações Padrão para Orçamentos', blank=True)
    
    class Meta:
        verbose_name = 'Configuração da Empresa'
        verbose_name_plural = 'Configurações da Empresa'
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracaoEmpresa.objects.exists():
            return
        super().save(*args, **kwargs)
