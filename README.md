# EgonSystem v2 🚀

Sistema de análise de commits de repositórios GitHub com arquitetura de datalake e snapshots.

## 🔧 Configuração

### 1. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Configure no `.env`:
```env
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# Repositories Configuration (comma-separated list)
INTERNAL_REPOSITORIES=org/repo1-INTERNO,org/repo2-INTERNO
PUBLIC_REPOSITORIES=org/repo1-PUBLICO,org/repo2-PUBLICO

# Database Configuration
DATALAKE_PATH=./datalake
SNAPSHOTS_PATH=./datalake/snapshots

# Application Configuration
APP_NAME=EgonSystem
LOG_LEVEL=INFO
```

### 2. Executar com Docker

```bash
# Build e execução
docker-compose up --build

# Acessar em http://localhost:9990
```

### 3. Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py

# Executar coleta manual
python scripts/collect_data.py
```

## 🏗️ Arquitetura

### DataLake Structure
```
/datalake/
  /snapshots/
    /snapshot_2025-06-21_14-30-00/
      repositories.parquet
      commits.parquet
      pull_requests.parquet
      metadata.json
```

### Componentes Principais

- **DataCollector**: Coleta dados do GitHub
- **DataLake**: Gerencia snapshots em formato Parquet
- **GitHubClient**: Interface com API do GitHub
- **Config**: Gerenciamento de configurações

## 🎯 Funcionalidades

### ✅ Dashboard Web
- 📊 Overview com métricas gerais
- ❌ Repositórios sem commits na janela
- ⚠️ Repositórios com commits após a janela
- 🔍 Detalhamento por repositório

### ✅ Datalake
- 📸 Snapshots versionados
- 🗂️ Dados em formato Parquet
- 📊 Histórico de coletas
- 🔄 Recuperação de snapshots

### ✅ Botão de Atualização
- 🔄 Coleta todos os repositórios configurados
- ⚡ Processamento em paralelo
- 📊 Feedback em tempo real

## 🚀 Melhorias da v2

1. **Datalake com Snapshots**: Histórico versionado dos dados
2. **Configuração via .env**: Repositórios configuráveis
3. **Botão de Atualização Universal**: Um clique atualiza tudo
4. **Arquitetura OOP**: Código mais organizado e testável
5. **Formato Parquet**: Performance superior ao DuckDB
6. **Logging Estruturado**: Melhor rastreabilidade
7. **Docker Otimizado**: Deploy mais eficiente

## 📊 Comparação: v1 vs v2

| Funcionalidade | v1 | v2 |
|---|---|---|
| Repositórios | Hardcoded | Configurável via .env |
| Atualização | Manual script | Botão na interface |
| Armazenamento | DuckDB | Parquet (DataLake) |
| Snapshots | ❌ | ✅ |
| Overview | Básica | Completa com métricas |
| Arquitetura | Monolítica | Modular (OOP) |

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
src/
├── __init__.py
├── config.py          # Configurações
├── models.py           # Modelos de dados
├── github_client.py    # Cliente GitHub
├── datalake.py        # Gerenciamento do datalake
└── data_collector.py   # Coleta de dados

scripts/
└── collect_data.py     # Script de coleta manual

app.py                  # Interface Streamlit
```

### Próximos Passos
- [ ] Implementar testes unitários
- [ ] Adicionar filtros por autor
- [ ] Implementar alertas automáticos
- [ ] Dashboard de performance
- [ ] API REST para integração