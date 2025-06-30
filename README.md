# EgonSystem 🚀

Sistema de análise de commits e pull requests de repositórios GitHub com arquitetura de datalake em nuvem e snapshots históricos.

## O que é o FourSystem?

O **FourSystem** é uma plataforma de monitoramento e análise de repositórios GitHub desenvolvida para acompanhar a atividade de desenvolvimento de múltiplos repositórios simultaneamente. O sistema coleta dados de commits, pull requests e informações dos repositórios, armazenando-os em um datalake em nuvem (Supabase) para análise posterior.

### Principais características:
- **Monitoramento de múltiplos repositórios** GitHub em tempo real
- **Datalake em nuvem** com Supabase Storage para armazenamento escalável
- **Snapshots históricos** para análise temporal dos dados
- **Dashboard interativo** com métricas e visualizações
- **Coleta automatizada** de dados via API do GitHub
- **Arquitetura modular** para fácil manutenção e extensão

## 🔧 Configuração e Setup

### Pré-requisitos
- Python 3.8+
- Conta no GitHub com Personal Access Token
- Conta no Supabase (gratuita)
- Docker (opcional, para execução containerizada)

### 1. Configurar Supabase

1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Crie um novo projeto
3. Vá para **Storage** > **Buckets** e crie um bucket chamado `snapshots`
4. **IMPORTANTE**: Configure o bucket como público ou configure políticas de Storage (veja [SUPABASE_STORAGE_FIX.md](SUPABASE_STORAGE_FIX.md))
5. Anote a URL do projeto e a chave anônima

### 2. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Configure as seguintes variáveis no arquivo `.env`:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_personal_access_token_here

# Repositories Configuration (comma-separated list)
INTERNAL_REPOSITORIES=Inteli-College/2025-1A-T01-G01-INTERNO,Inteli-College/2025-1A-T01-G02-INTERNO
PUBLIC_REPOSITORIES=Inteli-College/2025-1A-T01-G01-PUBLICO,Inteli-College/2025-1A-T01-G02-PUBLICO

# Application Configuration
APP_NAME=FourSystem
LOG_LEVEL=INFO

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_BUCKET=snapshots
```

### 3. Obter Token do GitHub

1. Acesse [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Clique em "Generate new token (classic)"
3. Selecione os escopos necessários:
   - `repo` (para repositórios privados)
   - `public_repo` (para repositórios públicos)
   - `user:email` (para acessar emails dos usuários)
4. Copie o token gerado e adicione no arquivo `.env`

### 4. Instalar Dependências

```bash
# Instalar dependências Python
pip install -r requirements.txt
```

### 5. Executar o Sistema

#### Opção A: Execução Local
```bash
# Executar aplicação Streamlit
streamlit run app.py

# Acesse http://localhost:8501
```

#### Opção B: Execução com Docker
```bash
# Build e execução com Docker Compose
docker-compose up --build

# Acesse http://localhost:9990
```

## 🏗️ Arquitetura do Sistema

### Estrutura do Datalake (Supabase Storage)
```
/snapshots/ (bucket)
├── snapshot_2025-06-23_14-30-00/
│   ├── repositories.parquet
│   ├── commits.parquet
│   ├── pull_requests.parquet
│   └── metadata.json
├── snapshot_2025-06-23_15-45-00/
│   ├── repositories.parquet
│   ├── commits.parquet
│   ├── pull_requests.parquet
│   └── metadata.json
└── ...
```

### Componentes Principais

#### 1. **DataCollector** (`src/data_collector.py`)
- Coleta dados de repositórios, commits e pull requests
- Processa dados em paralelo para otimizar performance
- Integra com GitHub API

#### 2. **DataLake** (`src/datalake.py`)
- Gerencia snapshots em Supabase Storage
- Salva dados em formato Parquet para performance
- Controla versionamento e histórico

#### 3. **GitHubClient** (`src/github_client.py`)
- Interface com a API do GitHub
- Gerencia autenticação e rate limiting
- Extrai dados de repositórios, commits e PRs

#### 4. **Config** (`src/config.py`)
- Gerencia configurações via variáveis de ambiente
- Valida credenciais e parâmetros
- Configura conexões com serviços externos

#### 5. **Models** (`src/models.py`)
- Define estruturas de dados (Repository, Commit, PullRequest)
- Padroniza formato dos dados coletados
- Facilita serialização/deserialização

## 🎯 Funcionalidades

### ✅ Dashboard Web Interativo
- **📊 Overview geral** com métricas consolidadas
- **📈 Gráficos temporais** de atividade
- **🔍 Filtros por repositório** e período
- **📋 Listas detalhadas** de commits e PRs
- **🔄 Botão de atualização** em tempo real

### ✅ Datalake em Nuvem
- **📸 Snapshots versionados** com timestamp
- **☁️ Armazenamento em Supabase** Storage
- **🗂️ Formato Parquet** para alta performance
- **📊 Histórico completo** de todas as coletas
- **🔄 Recuperação de snapshots** antigos

### ✅ Coleta Automatizada
- **⚡ Processamento paralelo** de repositórios
- **🔄 Atualização com um clique**
- **📊 Feedback visual** do progresso
- **⏱️ Controle de rate limiting** da API

### ✅ Monitoramento Avançado
- **🔍 Análise de padrões** de commits
- **👥 Tracking de contribuidores**
- **📈 Métricas de atividade** por período
- **⚠️ Alertas visuais** para repositórios inativos

## 🚀 Guia de Uso

### 1. Primeira Execução
1. Configure as variáveis de ambiente
2. Execute o sistema
3. Clique em "Atualizar Dados" para fazer a primeira coleta
4. Aguarde o processamento (pode demorar alguns minutos)

### 2. Navegação no Dashboard
- **Overview**: Métricas gerais e gráficos
- **Repositórios**: Lista detalhada por repositório
- **Commits**: Análise de commits por período
- **Pull Requests**: Tracking de PRs abertos/fechados

### 3. Análise de Dados
- Use os filtros para focar em períodos específicos
- Analise tendências nos gráficos temporais
- Identifique repositórios com baixa atividade
- Monitore contribuidores mais ativos

## 🛠️ Desenvolvimento e Manutenção

### Estrutura do Projeto
```
egonsystem/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configurações do sistema
│   ├── models.py          # Modelos de dados
│   ├── github_client.py   # Cliente GitHub API
│   ├── datalake.py        # Gerenciamento do datalake
│   └── data_collector.py  # Coleta de dados
├── .env.example           # Exemplo de configuração
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
├── app.py               # Interface Streamlit
└── README.md           # Documentação
```

### Adicionando Novos Repositórios
1. Edite o arquivo `.env`
2. Adicione os repositórios nas listas `INTERNAL_REPOSITORIES` ou `PUBLIC_REPOSITORIES`
3. Reinicie o sistema
4. Execute uma nova coleta de dados

### Monitoramento e Logs
- Logs são exibidos no console durante a execução
- Nível de log configurável via `LOG_LEVEL`
- Métricas de performance disponíveis no dashboard

## 🔒 Segurança e Boas Práticas

### Proteção de Credenciais
- **Nunca commitar** tokens em repositórios
- Usar variáveis de ambiente para credenciais
- Rotacionar tokens periodicamente
- Configurar escopos mínimos necessários

### Rate Limiting
- Sistema respeita limits da API do GitHub
- Implementa retry automático quando necessário
- Monitora uso de quota da API

### Backup e Recuperação
- Snapshots são automaticamente versionados
- Dados armazenados em nuvem com alta disponibilidade
- Possibilidade de recuperar dados históricos

## 📊 Performance e Escalabilidade

### Otimizações Implementadas
- **Formato Parquet**: 10x mais rápido que CSV
- **Processamento paralelo**: Múltiplos repositórios simultaneamente
- **Cache inteligente**: Evita requests desnecessários
- **Compressão automática**: Reduz uso de storage

### Limites e Capacidade
- **Repositórios**: Ilimitados (limitado pela API do GitHub)
- **Histórico**: Ilimitado (limitado pelo storage do Supabase)
- **Concurrent requests**: Respeitam rate limits da API
- **Storage**: Escalável conforme plano do Supabase

## 🆘 Troubleshooting

### Problemas Comuns

#### Erro de Autenticação GitHub
```
Erro: 401 Unauthorized
Solução: Verificar se o GITHUB_TOKEN está correto e ativo
```

#### Erro de Conexão Supabase
```
Erro: Bucket not found
Solução: Criar bucket 'snapshots' no painel do Supabase
```

#### Erro de Permissão Supabase Storage
```
Erro: {'statusCode': 403, 'error': Unauthorized, 'message': new row violates row-level security policy}
Solução: Configurar bucket como público ou políticas de Storage - veja SUPABASE_STORAGE_FIX.md
```

#### Erro de Rate Limit
```
Erro: API rate limit exceeded
Solução: Aguardar reset ou usar token com quota maior
```

### Logs de Debug
Para debug detalhado, configure `LOG_LEVEL=DEBUG` no arquivo `.env`.

## 🔮 Próximos Passos

### Funcionalidades Planejadas
- [ ] **Alertas por email** para repositórios inativos
- [ ] **API REST** para integração externa
- [ ] **Dashboard mobile** responsivo
- [ ] **Exportação de relatórios** em PDF/Excel
- [ ] **Análise de código** com métricas de qualidade
- [ ] **Integração com Slack/Teams** para notificações
- [ ] **Machine Learning** para predição de atividade

### Melhorias Técnicas
- [ ] **Testes unitários** completos
- [ ] **CI/CD pipeline** automatizado
- [ ] **Monitoramento de performance** em produção
- [ ] **Cache distribuído** para maior performance
- [ ] **Autenticação de usuários** multi-tenant

---

**Desenvolvido com ❤️ para monitoramento eficiente de repositórios GitHub**
