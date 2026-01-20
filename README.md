# Sistema de Gestão - Tornearia Jair

Sistema completo de gestão empresarial para tornearia, desenvolvido em Django com interface moderna usando TailwindCSS.

## Funcionalidades

- **Dashboard Analítico**: Métricas de receitas, despesas e lucro com gráficos interativos
- **Gestão de Clientes e Empresas**: Cadastro completo de pessoas físicas e jurídicas
- **Gestão de Funcionários**: Controle de funcionários e salários
- **Serviços e Estoque**: Cadastro de serviços e produtos com controle de estoque
- **Sistema de Orçamentos**: Criação, aprovação e conversão em vendas com geração de PDF
- **Controle Financeiro**: Vendas, despesas e categorização
- **Relatórios**: Filtros por período e análises detalhadas

## Tecnologias

- **Backend**: Django 5.0
- **Frontend**: HTML + TailwindCSS (via CDN) + Alpine.js
- **Banco de Dados**: SQLite (dev) / PostgreSQL (produção)
- **PDF**: ReportLab
- **Gráficos**: Chart.js

## Instalação Local

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd Jair-Project
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Execute as migrações
```bash
python manage.py migrate
```

### 6. Crie o superusuário
```bash
python manage.py createsuperuser
```

### 7. Inicie o servidor de desenvolvimento
```bash
python manage.py runserver
```

Acesse http://localhost:8000

## Deploy no Railway

### 1. Crie uma conta no Railway
Acesse [railway.app](https://railway.app) e crie uma conta.

### 2. Crie um novo projeto
- Clique em "New Project"
- Selecione "Deploy from GitHub repo"
- Conecte seu repositório

### 3. Adicione um banco PostgreSQL
- No projeto, clique em "New"
- Selecione "Database" > "PostgreSQL"

### 4. Configure as variáveis de ambiente
No serviço da aplicação, adicione as seguintes variáveis:

```
SECRET_KEY=<gere-uma-chave-segura>
DEBUG=False
ALLOWED_HOSTS=seu-dominio.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Para gerar uma SECRET_KEY segura:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 5. Deploy automático
O Railway fará o deploy automaticamente quando você fizer push para o repositório.

## Estrutura do Projeto

```
Jair-Project/
├── config/              # Configurações do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/           # Dashboard e configurações
│   ├── cadastros/      # Clientes, empresas, funcionários
│   ├── servicos/       # Serviços e estoque
│   ├── orcamentos/     # Sistema de orçamentos
│   └── financeiro/     # Vendas e despesas
├── templates/          # Templates HTML
├── static/             # Arquivos estáticos
├── requirements.txt
├── Procfile           # Para deploy no Railway
└── runtime.txt        # Versão do Python
```

## Uso do Sistema

### Primeiro Acesso
1. Faça login com o superusuário criado
2. Acesse "Configurações" para cadastrar os dados da empresa
3. Cadastre categorias de despesas
4. Cadastre serviços e produtos
5. Cadastre clientes e empresas

### Fluxo de Trabalho
1. **Orçamento**: Crie orçamentos para clientes
2. **Aprovação**: Cliente aprova o orçamento
3. **Conversão**: Converta o orçamento em venda
4. **Execução**: Acompanhe o serviço em andamento
5. **Conclusão**: Conclua a venda (atualiza estoque automaticamente)

### Dashboard
- Filtros por período (dia, semana, mês, ano)
- Métricas de receitas, despesas e lucro
- Gráficos de evolução e distribuição
- Acesso rápido a vendas em andamento e orçamentos pendentes

## Backup

Para fazer backup do banco de dados:
```bash
python manage.py dumpdata > backup.json
```

Para restaurar:
```bash
python manage.py loaddata backup.json
```

## Suporte

Sistema desenvolvido por solicitação de Jair para gestão de sua tornearia.

---

**Versão**: 1.0.0  
**Django**: 5.0.1  
**Python**: 3.11+
