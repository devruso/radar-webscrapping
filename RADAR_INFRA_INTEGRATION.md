# 🔗 Integração com Radar-Infra

Instruções específicas para integração do **radar-webscrapping** com o repositório **radar-infra**.

## 📋 Visão Geral da Integração

O **radar-infra** é o repositório de orquestração que contém:
- Docker Compose para todos os 4 componentes
- Configurações de rede e volumes
- Scripts de deploy e manutenção
- Configurações de ambiente unificadas

## 🏗️ Estrutura Esperada no radar-infra

```
radar-infra/
├── docker-compose.yml           # ✅ Já configurado com radar-webscrapping
├── .env.example                # Configure as variáveis necessárias  
├── .env                        # Copie e ajuste do .env.example
├── scripts/
│   ├── init-db/               # Scripts de inicialização do MySQL
│   └── deploy.sh              # Deploy automatizado
├── radar-webscrapping/         # 📁 Este repositório (submodule)
├── radar-webapi/              # 📁 Backend Spring Boot
├── radar-webapp/              # 📁 Frontend React
└── README.md                  # Instruções do sistema completo
```

## 🔧 Setup no radar-infra

### 1. Clonar como Submodule

No repositório **radar-infra**:

```bash
# Adicionar como submodule
git submodule add <radar-webscrapping-repo-url> radar-webscrapping

# Atualizar submodules
git submodule update --init --recursive

# Commit da adição
git add .gitmodules radar-webscrapping
git commit -m "feat: adicionar radar-webscrapping como submodule"
```

### 2. Configurar .env no radar-infra

Adicione estas variáveis ao `.env` do **radar-infra**:

```env
# =============================================================================
# RADAR WEBSCRAPPING - CONFIGURAÇÕES
# =============================================================================

# Versão da imagem Docker
WEBSCRAPPING_VERSION=latest

# Porta de exposição
WEBSCRAPPING_PORT=8000

# Configurações de integração com radar-webapi
RADAR_API_KEY=your-secure-production-api-key-here

# Agendamento automático (cron expression)
# Padrão: Todo dia às 2h da manhã
SCRAPING_SCHEDULE=0 2 * * *

# Nível de log para scraping
SCRAPING_LOG_LEVEL=INFO

# URL para o frontend (opcional)
VITE_WEBSCRAPPING_URL=http://localhost:8000

# Configurações específicas de performance
SCRAPING_CONCURRENT_LIMIT=3
SCRAPING_BATCH_SIZE=10
SCRAPING_TIMEOUT=300
```

### 3. Verificar docker-compose.yml

O **docker-compose.yml** do **radar-infra** já deve conter:

```yaml
# Scrapers - Python FastAPI
radar-webscrapping:
  build: 
    context: ./radar-webscrapping
    dockerfile: Dockerfile
  image: radar/webscrapping:${WEBSCRAPPING_VERSION:-latest}
  container_name: radar-webscrapping
  restart: unless-stopped
  ports:
    - "${WEBSCRAPPING_PORT:-8000}:8000"
  environment:
    RADAR_API_URL: http://radar-webapi:8080
    RADAR_API_KEY: ${RADAR_API_KEY}
    SCRAPING_SCHEDULE: ${SCRAPING_SCHEDULE:-0 2 * * *}
    LOG_LEVEL: ${SCRAPING_LOG_LEVEL:-INFO}
  depends_on:
    radar-webapi:
      condition: service_healthy
  networks:
    - radar-network
  volumes:
    - scraping_data:/app/data
    - scraping_logs:/app/logs
```

## 🚀 Deploy Completo

### 1. Preparação

```bash
# No diretório radar-infra
cd radar-infra

# Atualizar submodules
git submodule update --remote --merge

# Verificar estrutura
ls -la
# Deve conter: radar-webscrapping, radar-webapi, radar-webapp
```

### 2. Configuração

```bash
# Copiar configuração exemplo
cp .env.example .env

# Editar configurações
vim .env  # ou seu editor preferido

# Verificar configuração do webscrapping
grep WEBSCRAPPING .env
```

### 3. Build e Deploy

```bash
# Build de todas as imagens
docker-compose build

# Deploy completo (primeira vez)
docker-compose up -d

# Verificar status
docker-compose ps
```

### 4. Verificação

```bash
# Health check de todos os serviços
curl http://localhost:3306  # MySQL
curl http://localhost:8080/actuator/health  # WebAPI
curl http://localhost:8000/health           # WebScrapping  
curl http://localhost:3000                  # WebApp

# Logs do webscrapping
docker-compose logs -f radar-webscrapping
```

## 🔄 Fluxo de Dados Integrado

### 1. Coleta (WebScrapping)
```
SIGAA UFBA → radar-webscrapping → Dados estruturados
```

### 2. Processamento (WebAPI)
```
radar-webscrapping → radar-webapi → MySQL
```

### 3. Apresentação (WebApp)
```
MySQL → radar-webapi → radar-webapp → Usuário
```

### 4. Agendamento
```
Cron (2h) → radar-webscrapping → Coleta automática
```

## 🛠️ Comandos de Manutenção

### Atualizar WebScrapping

```bash
# No radar-infra
cd radar-webscrapping
git pull origin main
cd ..

# Rebuild e redeploy
docker-compose build radar-webscrapping
docker-compose up -d radar-webscrapping
```

### Logs e Monitoring

```bash
# Logs de todos os componentes
docker-compose logs -f

# Logs apenas do webscrapping
docker-compose logs -f radar-webscrapping

# Logs com filtro
docker-compose logs radar-webscrapping | grep ERROR

# Status detalhado
docker-compose ps
docker stats
```

### Backup de Dados

```bash
# Backup dos dados de scraping
docker run --rm \
  -v radar-infra_scraping_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/scraping-data-$(date +%Y%m%d).tar.gz -C /data .

# Backup dos logs
docker run --rm \
  -v radar-infra_scraping_logs:/logs \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/scraping-logs-$(date +%Y%m%d).tar.gz -C /logs .
```

### Execução Manual de Scraping

```bash
# Scraping de cursos específico
docker-compose exec radar-webscrapping python main.py scrape-cursos --unidade "IME"

# Scraping completo
docker-compose exec radar-webscrapping python main.py scrape-completo

# Status do sistema
docker-compose exec radar-webscrapping python main.py status
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia
```bash
# Verificar logs
docker-compose logs radar-webscrapping

# Verificar dependências
docker-compose ps
# radar-webapi deve estar "healthy"

# Verificar rede
docker network ls | grep radar
```

#### 2. Erro de conexão com WebAPI
```bash
# Testar conectividade interna
docker-compose exec radar-webscrapping curl http://radar-webapi:8080/actuator/health

# Verificar variáveis de ambiente
docker-compose exec radar-webscrapping env | grep RADAR_API
```

#### 3. Scraping não funciona
```bash
# Executar manualmente para debug
docker-compose exec radar-webscrapping python main.py scrape-cursos --debug

# Verificar Chrome/ChromeDriver
docker-compose exec radar-webscrapping google-chrome --version
docker-compose exec radar-webscrapping chromedriver --version
```

#### 4. Performance issues
```bash
# Verificar recursos
docker stats radar-webscrapping

# Ajustar limits no docker-compose.yml
```

### Debug Avançado

```bash
# Shell no container
docker-compose exec radar-webscrapping bash

# Python REPL
docker-compose exec radar-webscrapping python

# Ver configurações carregadas
docker-compose exec radar-webscrapping python -c "
from src.shared.config import Config
config = Config()
print(f'Database: {config.database_url}')
print(f'API URL: {config.radar_api_base_url}')
"
```

## 📊 Monitoramento em Produção

### Health Checks

Todos os health checks estão configurados:

```bash
# WebScrapping
curl http://localhost:8000/health

# Verificar status no docker-compose
docker-compose ps
# STATUS deve ser "Up (healthy)"
```

### Métricas

```bash
# Métricas básicas
curl http://localhost:8000/metrics

# Status dos jobs
curl http://localhost:8000/api/jobs/status

# Estatísticas de scraping
curl http://localhost:8000/api/stats
```

### Alertas Recomendados

Configure alertas para:
- Container parado ou unhealthy
- Alto uso de memória (>1GB)
- Falhas consecutivas de scraping
- Logs de ERROR
- Disk space dos volumes

## 🚀 Deploy em Produção

### Configurações de Produção

```env
# .env para produção
APP_ENV=production
LOG_LEVEL=INFO
LOG_FORMAT=json

# Recursos limitados
SCRAPING_CONCURRENT_LIMIT=2
SCRAPING_TIMEOUT=180

# Security
RADAR_API_KEY=super-secure-production-key

# Performance
SELENIUM_HEADLESS=true
DATABASE_POOL_SIZE=10
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml (exemplo)
name: Deploy Radar Infra
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml up -d
          docker-compose ps
```

## 📝 Checklist de Integração

- [ ] radar-webscrapping adicionado como submodule
- [ ] .env configurado com variáveis do webscrapping
- [ ] docker-compose.yml contém configuração do radar-webscrapping
- [ ] Build funciona: `docker-compose build radar-webscrapping`
- [ ] Deploy funciona: `docker-compose up -d`
- [ ] Health check passa: `curl http://localhost:8000/health`
- [ ] Integração com WebAPI funciona
- [ ] Logs aparecem: `docker-compose logs radar-webscrapping`
- [ ] Volumes persistem dados em `/app/data` e `/app/logs`
- [ ] Rede permite comunicação entre serviços

---

**Sistema Radar - Integração Completa** 🎯  
**Todos os 4 componentes funcionando em harmonia** ⚙️