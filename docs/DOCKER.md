# 🐳 Docker - Radar WebScrapping

Guia completo para execução do Radar WebScrapping em Docker.

## 📋 Visão Geral

O sistema está totalmente containerizado e pronto para:
- **Desenvolvimento local** com docker-compose
- **Integração com radar-infra** para produção
- **Execução isolada** para testes

## 🏗️ Estrutura dos Arquivos Docker

```
radar-webscrapping/
├── Dockerfile                 # Imagem principal
├── .dockerignore             # Arquivos excluídos do build
├── docker-compose.yml        # Ambiente completo local
├── scripts/
│   └── docker-entrypoint.sh  # Script de inicialização
└── .env.example              # Variáveis de ambiente
```

## 🔧 Build e Execução Local

### Build da Imagem

```bash
# Build simples
docker build -t radar/webscrapping .

# Build com argumentos
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t radar/webscrapping:dev .

# Build sem cache
docker build --no-cache -t radar/webscrapping .
```

### Execução Simples

```bash
# Executar CLI
docker run --rm -it radar/webscrapping cli --help

# Executar API
docker run -p 8000:8000 radar/webscrapping api

# Executar scraping específico
docker run --rm radar/webscrapping scrape-cursos --unidade "IME"

# Shell interativo
docker run --rm -it radar/webscrapping bash
```

## 🚀 Docker Compose - Desenvolvimento

### Iniciar Ambiente Completo

```bash
# Subir todos os serviços
docker-compose up -d

# Subir com rebuild
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Ver status
docker-compose ps
```

### Serviços Disponíveis

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| webscrapping | 8000 | Aplicação principal |
| postgres | 5432 | Banco de dados |
| redis | 6379 | Cache |
| pgadmin | 5050 | Admin PostgreSQL |
| jupyter | 8888 | Análise de dados |

### Comandos Úteis

```bash
# Executar comando no container
docker-compose exec webscrapping python main.py status

# Acessar shell do container
docker-compose exec webscrapping bash

# Ver logs específicos
docker-compose logs webscrapping

# Reiniciar serviço específico
docker-compose restart webscrapping

# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

## 🏢 Integração com radar-infra

### Estrutura no radar-infra

```
radar-infra/
├── docker-compose.yml         # Orquestração completa
├── .env                      # Configurações de produção
├── radar-webscrapping/       # Este repositório como submodule
├── radar-webapi/            # API Spring Boot
├── radar-webapp/            # Frontend React
└── scripts/
    └── deploy.sh            # Script de deploy
```

### Configuração no radar-infra

O serviço já está configurado no docker-compose do radar-infra:

```yaml
radar-webscrapping:
  build: 
    context: ./radar-webscrapping
    dockerfile: Dockerfile
  image: radar/webscrapping:${WEBSCRAPPING_VERSION:-latest}
  container_name: radar-webscrapping
  environment:
    RADAR_API_URL: http://radar-webapi:8080
    RADAR_API_KEY: ${RADAR_API_KEY}
    SCRAPING_SCHEDULE: ${SCRAPING_SCHEDULE:-0 2 * * *}
  depends_on:
    radar-webapi:
      condition: service_healthy
  volumes:
    - scraping_data:/app/data
    - scraping_logs:/app/logs
```

### Variáveis de Ambiente (radar-infra)

Configure no `.env` do radar-infra:

```env
# Versões
WEBSCRAPPING_VERSION=latest
WEBSCRAPPING_PORT=8000

# Integração
RADAR_API_KEY=secure-api-key-production
SCRAPING_SCHEDULE=0 2 * * *
SCRAPING_LOG_LEVEL=INFO

# Opcional - Para desenvolvimento
VITE_WEBSCRAPPING_URL=http://localhost:8000
```

## 🎯 Modos de Execução

O entrypoint suporta diferentes modos:

### API Mode (Padrão)
```bash
docker run -p 8000:8000 radar/webscrapping
# ou explicitamente
docker run -p 8000:8000 radar/webscrapping api
```

### CLI Mode
```bash
# Help
docker run --rm radar/webscrapping cli --help

# Scraping específico
docker run --rm radar/webscrapping cli scrape-cursos --unidade "IME"

# Status do sistema
docker run --rm radar/webscrapping cli status
```

### Scraping Direto
```bash
# Scraping de cursos
docker run --rm radar/webscrapping scrape-cursos

# Scraping de componentes
docker run --rm radar/webscrapping scrape-componentes

# Scraping de estruturas
docker run --rm radar/webscrapping scrape-estruturas
```

### Background Services
```bash
# Scheduler (agendamento automático)
docker run -d radar/webscrapping scheduler

# Worker (processamento background)
docker run -d radar/webscrapping worker
```

### Desenvolvimento
```bash
# Shell bash
docker run --rm -it radar/webscrapping bash

# Python REPL
docker run --rm -it radar/webscrapping python

# Jupyter notebook
docker-compose up jupyter
```

## 🔍 Debugging e Troubleshooting

### Health Check

```bash
# Status do container
docker ps

# Detalhes do health check
docker inspect --format='{{json .State.Health}}' radar-webscrapping

# Logs do health check
docker logs radar-webscrapping | grep health
```

### Logs Detalhados

```bash
# Logs em tempo real
docker-compose logs -f webscrapping

# Últimas 100 linhas
docker-compose logs --tail=100 webscrapping

# Logs com timestamp
docker-compose logs -t webscrapping

# Filtrar logs
docker-compose logs webscrapping | grep ERROR
```

### Debug Container

```bash
# Acessar container em execução
docker exec -it radar-webscrapping bash

# Verificar processos
docker exec radar-webscrapping ps aux

# Ver variáveis de ambiente
docker exec radar-webscrapping env

# Testar conectividade
docker exec radar-webscrapping curl http://localhost:8000/health
```

### Volumes e Dados

```bash
# Listar volumes
docker volume ls | grep radar

# Inspecionar volume
docker volume inspect radar-webscrapping_scraping_data

# Backup de dados
docker run --rm -v radar-webscrapping_scraping_data:/data -v $(pwd):/backup ubuntu tar czf /backup/data-backup.tar.gz -C /data .

# Restore de dados
docker run --rm -v radar-webscrapping_scraping_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/data-backup.tar.gz -C /data
```

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente Importantes

```env
# Docker específicas
DOCKER_ENV=true
CHROME_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Performance
SCRAPING_CONCURRENT_LIMIT=3
SCRAPING_BATCH_SIZE=20

# Selenium
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Resource Limits

```yaml
# No docker-compose.yml
services:
  webscrapping:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Network Configuration

```yaml
# Para acesso externo ao SIGAA
networks:
  radar-network:
    driver: bridge
    internal: false  # Permite acesso à internet
```

## 🚀 Deploy em Produção

### Com radar-infra

```bash
# 1. Clone radar-infra
git clone <radar-infra-repo>
cd radar-infra

# 2. Configure .env para produção
cp .env.example .env
vim .env

# 3. Deploy completo
docker-compose -f docker-compose.prod.yml up -d

# 4. Verificar status
docker-compose ps
curl http://your-domain:8000/health
```

### Deploy Isolado

```bash
# Build para produção
docker build -t radar/webscrapping:prod .

# Run com configurações de produção
docker run -d \
  --name radar-webscrapping \
  --restart unless-stopped \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql://... \
  -e RADAR_API_URL=https://api.radar.ufba.br \
  -v /var/log/radar:/app/logs \
  radar/webscrapping:prod
```

## 📊 Monitoramento

### Métricas

```bash
# Uso de recursos
docker stats radar-webscrapping

# Logs estruturados
docker logs radar-webscrapping | jq '.'

# Health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Alertas

Configure alertas para:
- Container parado
- High memory usage
- Failed health checks
- Scraping errors

## 🔧 Desenvolvimento

### Hot Reload (Desenvolvimento)

```yaml
# docker-compose.override.yml
services:
  webscrapping:
    volumes:
      - ./src:/app/src:ro
      - ./main.py:/app/main.py:ro
    environment:
      - RELOAD_ON_CHANGE=true
```

### Tests

```bash
# Executar testes no container
docker-compose exec webscrapping pytest

# Com cobertura
docker-compose exec webscrapping pytest --cov=src

# Testes específicos
docker-compose exec webscrapping pytest tests/unit/
```

---

**Desenvolvido para integração completa com o Sistema Radar** 🎯