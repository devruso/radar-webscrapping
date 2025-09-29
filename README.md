# 🎯 Radar WebScrapping

Sistema de coleta automatizada de dados acadêmicos do SIGAA UFBA, desenvolvido seguindo **Clean Architecture** e princípios **SOLID**.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Architecture](https://img.shields.io/badge/Architecture-Clean-green.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
[![SOLID](https://img.shields.io/badge/Principles-SOLID-orange.svg)](https://en.wikipedia.org/wiki/SOLID)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema robusto e escalável para coleta de dados acadêmicos do SIGAA UFBA, fornecendo informações estruturadas sobre cursos, componentes curriculares e estruturas curriculares para o sistema Radar de recomendação acadêmica.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura Clean](#arquitetura-clean)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Docker](#docker)
5. [Guia de Uso](#guia-de-uso)
6. [Desenvolvimento](#desenvolvimento)
7. [Integração Radar-Infra](#integração-radar-infra)
8. [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

O **Radar WebScrapping** é o componente de coleta de dados do Sistema Radar de Recomendação Acadêmica da UFBA. Desenvolvido seguindo **Clean Architecture** e princípios **SOLID**, oferece:

### 🔧 Funcionalidades Principais

- **📚 Scraping de Cursos**: Coleta dados dos cursos de graduação do SIGAA UFBA
- **📋 Componentes Curriculares**: Extração de disciplinas e atividades acadêmicas  
- **🏗️ Estruturas Curriculares**: Mapeamento de grades curriculares e pré-requisitos
- **🔄 Sincronização**: Integração automática com radar-webapi (Spring Boot)
- **💻 Interface CLI**: Controle completo via linha de comando
- **🐳 Docker Ready**: Containerização para deploy simplificado

### ✨ Características Técnicas

✅ **Clean Architecture**: Separação clara de responsabilidades em camadas  
✅ **SOLID Principles**: Código maintível e extensível  
✅ **Async/Await**: Operações assíncronas para melhor performance  
✅ **SQLAlchemy ORM**: Persistência de dados robusta  
✅ **Selenium WebDriver**: Automação web confiável  
✅ **Structured Logging**: Observabilidade com Loguru  
✅ **Type Safety**: Validação com Pydantic  

## 🏗️ Arquitetura Clean

O sistema segue rigorosamente os princípios de **Clean Architecture**:

```
┌─────────────────────────────────────────────────────┐
│                 INTERFACES                          │
│    CLI Controllers | REST API | Web Interface      │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│               APPLICATION                           │
│   Use Cases | DTOs | Repository Interfaces         │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                  DOMAIN                             │
│     Entities | Value Objects | Domain Logic        │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│              INFRASTRUCTURE                         │
│   Scrapers | Repositories | External APIs          │
└─────────────────────────────────────────────────────┘
```

### 📂 Estrutura de Diretórios

```
src/
├── domain/                    # 🔵 Camada de Domínio
│   ├── entities/             # Entidades de negócio
│   ├── value_objects/        # Objetos de valor
│   └── exceptions/           # Exceções de domínio
├── application/              # 🟡 Camada de Aplicação  
│   ├── use_cases/            # Casos de uso
│   ├── interfaces/           # Contratos/Abstrações
│   └── dtos/                 # Data Transfer Objects
├── infrastructure/           # 🔴 Camada de Infraestrutura
│   ├── scrapers/            # Implementações de scraping
│   ├── repositories/        # Persistência de dados
│   └── api_clients/         # Clientes HTTP
├── interfaces/              # 🟢 Camada de Interface
│   └── cli/                 # Controllers CLI
└── shared/                  # 🟠 Utilitários
    └── logging.py           # Configuração de logs
```

```python
scraper = scraper_registry.create_scraper(ScrapingType.COURSES)
```

#### 3. Observer Pattern
Monitoramento de progresso:

```python
class ScrapingJob:
    def notify_progress(self, progress):
        for observer in self.observers:
            observer.update(progress)
```

### Técnicas Anti-Detecção

#### 1. User Agent Rotation
```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
]
```

#### 2. Rate Limiting
```python
await asyncio.sleep(random.uniform(1, 3))  # Delay aleatório
```

#### 3. Headers Customizados
```python
headers = {
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1'
}
```

### Processamento de PDFs

#### Bibliotecas Utilizadas

1. **pdfplumber**: Melhor para textos estruturados
2. **PyMuPDF**: Melhor para layouts complexos

```python
# Estratégia dupla
pdfplumber_text = extract_with_pdfplumber(pdf_path)
pymupdf_text = extract_with_pymupdf(pdf_path)

# Escolher melhor resultado baseado em score de confiança
best_text = choose_best_extraction(pdfplumber_text, pymupdf_text)
```

## 🏗️ Arquitetura do Sistema

### Estrutura de Diretórios

```
radar-webscrapping/
├── src/
│   ├── models/           # Modelos de dados Pydantic
│   │   └── scraped_data.py
│   ├── scrapers/         # Scrapers especializados
│   │   ├── base_scraper.py
│   │   ├── course_scraper.py
│   │   ├── schedule_scraper.py
│   │   └── syllabus_scraper.py
│   ├── services/         # Serviços de infraestrutura
│   │   ├── api_client.py
│   │   └── pdf_processor.py
│   ├── utils/            # Utilitários
│   │   ├── browser_manager.py
│   │   └── data_validator.py
│   ├── config/           # Configurações
│   │   └── settings.py
│   └── main.py           # API FastAPI
├── requirements.txt
├── setup.py             # Script de configuração
├── run.py              # Inicializador
└── README.md
```

### Fluxo de Dados

1. **Configuração**: Carregamento de settings e inicialização
2. **Scraping**: Coleta de dados dos sites universitários
3. **Processamento**: Limpeza e estruturação dos dados
4. **Validação**: Verificação de qualidade e completude
5. **Sincronização**: Envio para backend via API REST

### Componentes Principais

#### 1. Browser Manager
Gerencia instâncias do Playwright com configurações anti-detecção:

```python
browser_manager = BrowserManager()
page = await browser_manager.get_page()
```

#### 2. Scraper Registry
Factory para criação e gerenciamento de scrapers:

```python
scraper_registry.register(CourseScraper)
scraper = scraper_registry.create_scraper(ScrapingType.COURSES)
```

#### 3. API Client
Cliente HTTP para comunicação com backend:

```python
await api_client.send_courses(courses_data)
await api_client.send_schedules(schedules_data)
```

#### 4. PDF Processor
Processamento inteligente de documentos PDF:

```python
content = await pdf_processor.extract_syllabus_content(pdf_path)
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- pip
- Conexão com internet

### Instalação Automática

```bash
# 1. Clone o repositório
git clone <repository-url>
cd radar-webscrapping

# 2. Execute o setup automático
python setup.py
```

O script `setup.py` irá:
- Instalar dependências Python
- Configurar navegadores Playwright
- Verificar configuração

### Instalação Manual

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Instalar navegadores Playwright
playwright install
playwright install-deps

# 3. Configurar ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### Configuração Local

Copie `.env.example` para `.env` e configure:

```env
# Configurações do SIGAA UFBA
SIGAA_BASE_URL=https://sigaa.ufba.br
SIGAA_DELAY_BETWEEN_REQUESTS=2.0

# Banco de dados local
DATABASE_URL=sqlite+aiosqlite:///data/radar_webscrapping.db

# API do Radar (integração)
RADAR_API_BASE_URL=http://localhost:8080/api
RADAR_API_TIMEOUT=30

# Selenium
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=30
```

## 🐳 Docker

O sistema está totalmente preparado para execução em Docker, com suporte completo ao **radar-infra**.

### 🔧 Desenvolvimento Local com Docker

```bash
# Clonar o repositório
git clone <repository-url>
cd radar-webscrapping

# Construir e executar com docker-compose
docker-compose up --build

# Serviços disponíveis:
# - App: http://localhost:8000
# - PostgreSQL: localhost:5432  
# - Redis: localhost:6379
# - PgAdmin: http://localhost:5050 (desenvolvimento)
# - Jupyter: http://localhost:8888 (desenvolvimento)
```

### 🏗️ Integração com radar-infra

Para execução no ambiente completo do sistema Radar:

1. **Clone o radar-infra**:
```bash
git clone <radar-infra-repository>
cd radar-infra
```

2. **Configure o .env do radar-infra**:
```env
# Versões
WEBSCRAPPING_VERSION=latest

# Configurações específicas
RADAR_API_KEY=your-production-api-key
SCRAPING_SCHEDULE=0 2 * * *  # 2h da manhã
SCRAPING_LOG_LEVEL=INFO
```

3. **Execute o sistema completo**:
```bash
docker-compose up -d
```

### 📦 Comandos Docker Disponíveis

```bash
# Executar CLI
docker run --rm -it radar/webscrapping:latest cli --help

# Scraping de cursos específico
docker run --rm radar/webscrapping:latest scrape-cursos --unidade "IME"

# Executar com todas as dependências
docker-compose run --rm webscrapping cli scrape-cursos

# Acessar container para debug
docker-compose exec webscrapping bash

# Ver logs em tempo real
docker-compose logs -f webscrapping
```

### 🎯 Modos de Execução

O container suporta diferentes modos através do **entrypoint**:

- **`api`**: Inicia servidor FastAPI (padrão)
- **`cli`**: Interface linha de comando
- **`scrape-cursos`**: Executa scraping de cursos
- **`scrape-componentes`**: Executa scraping de componentes
- **`scrape-estruturas`**: Executa scraping de estruturas
- **`scheduler`**: Inicia agendador automático
- **`worker`**: Inicia worker para processamento background

### 🔍 Health Check

O container inclui health check automático:

```bash
# Verificar status do container
docker ps

# Verificar logs do health check
docker inspect --format='{{json .State.Health}}' radar-webscrapping
```

## 📖 Guia de Uso

### Iniciar o Sistema

```bash
# Executar API em modo desenvolvimento
python run.py

# API estará disponível em http://localhost:8000
```

### Uso via API REST

#### 1. Verificar Status do Sistema

```bash
curl http://localhost:8000/health
```

#### 2. Listar Scrapers Disponíveis

```bash
curl http://localhost:8000/scrapers
```

#### 3. Executar Scraping Individual

```bash
curl -X POST http://localhost:8000/scraping/start \
  -H "Content-Type: application/json" \
  -d '{
    "scraping_type": "courses",
    "config": {"max_pages": 5},
    "send_to_backend": true
  }'
```

#### 4. Executar Scraping em Lote

```bash
curl -X POST http://localhost:8000/scraping/batch \
  -H "Content-Type: application/json" \
  -d '{
    "scraping_types": ["courses", "schedules", "syllabus"],
    "config": {"max_pages": 10},
    "max_concurrent": 2
  }'
```

#### 5. Monitorar Jobs

```bash
# Listar jobs
curl http://localhost:8000/scraping/jobs

# Status específico
curl http://localhost:8000/scraping/jobs/{job_id}

# Resultados
curl http://localhost:8000/scraping/results/{job_id}
```

### Uso Programático

```python
from src.scrapers.course_scraper import CourseScraper
from src.services.api_client import api_client

# Criar scraper
scraper = CourseScraper()

# Executar scraping
results = await scraper.scrape({
    'max_pages': 5,
    'search_terms': ['computação', 'engenharia']
})

# Enviar para backend
await api_client.send_courses(results)
```

## 👨‍💻 Desenvolvimento

### Criando um Novo Scraper

#### 1. Definir Modelo de Dados

```python
# src/models/scraped_data.py
class NewData(BaseScrapedData):
    field1: str
    field2: Optional[int] = None
    field3: List[str] = Field(default_factory=list)
```

#### 2. Implementar Scraper

```python
# src/scrapers/new_scraper.py
from .base_scraper import BaseScraper
from ..models.scraped_data import NewData, ScrapingType

class NewScraper(BaseScraper):
    def __init__(self):
        super().__init__(ScrapingType.NEW_TYPE)
    
    async def scrape(self, config: Dict[str, Any] = None) -> List[NewData]:
        # Implementar lógica de scraping
        results = []
        
        page = await browser_manager.get_page()
        await page.goto(self.base_url)
        
        # Extrair dados
        elements = await page.query_selector_all('.data-element')
        
        for element in elements:
            data = NewData(
                field1=await element.inner_text(),
                field2=42,
                field3=['item1', 'item2']
            )
            results.append(data)
        
        return results
```

#### 3. Registrar Scraper

```python
# src/main.py
from .scrapers.new_scraper import NewScraper

# No lifespan da aplicação
scraper_registry.register(NewScraper)
```

### Melhores Práticas

#### 1. Tratamento de Erros

```python
try:
    await page.goto(url, timeout=30000)
except PlaywrightTimeoutError:
    logger.error(f"Timeout ao carregar {url}")
    return []
except Exception as e:
    logger.error(f"Erro inesperado: {e}")
    raise
```

#### 2. Rate Limiting

```python
async def _apply_rate_limit(self):
    await asyncio.sleep(self.rate_limit + random.uniform(0, 1))
```

#### 3. Validação de Dados

```python
# Usar Pydantic para validação automática
class Course(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., regex=r'^[A-Z]{2,4}\d{3,4}$')
    credits: int = Field(..., ge=1, le=20)
```

#### 4. Logging Estruturado

```python
from loguru import logger

logger.info("Iniciando scraping", extra={
    "scraper": self.__class__.__name__,
    "url": url,
    "timestamp": datetime.now().isoformat()
})
```

### Debugging e Testes

#### 1. Modo Debug

```python
# Executar com browser visível
browser_manager = BrowserManager(headless=False)
```

#### 2. Screenshots para Debug

```python
await page.screenshot(path="debug_screenshot.png")
```

#### 3. Interceptar Requests

```python
async def intercept_request(request):
    logger.info(f"Request: {request.url}")

page.on("request", intercept_request)
```

## 📚 API Reference

### Endpoints Principais

#### GET /
Informações gerais da API

#### GET /health
Health check dos componentes

#### GET /scrapers
Lista scrapers disponíveis

#### POST /scraping/start
Inicia job individual
- `scraping_type`: Tipo do scraper
- `config`: Configurações específicas
- `send_to_backend`: Auto-sincronização

#### POST /scraping/batch
Inicia múltiplos jobs
- `scraping_types`: Lista de tipos
- `max_concurrent`: Limite de concorrência

#### GET /scraping/jobs
Lista jobs ativos
- `status`: Filtro por status
- `limit`: Limite de resultados

#### GET /scraping/jobs/{job_id}
Detalhes de job específico

#### GET /stats
Estatísticas do sistema

### Modelos de Dados

#### ScrapingJob
```python
{
    "job_id": "uuid",
    "scraping_type": "courses|schedules|syllabus",
    "status": "pending|running|completed|failed",
    "created_at": "2024-01-15T10:30:00",
    "config": {}
}
```

#### Course
```python
{
    "name": "Algoritmos e Estruturas de Dados",
    "code": "CIC0123",
    "credits": 4,
    "department": "Ciência da Computação",
    "prerequisites": ["CIC0456"],
    "description": "Estudo de algoritmos...",
    "source_url": "https://..."
}
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. "Browser não iniciou"
```bash
# Reinstalar navegadores
playwright install --force
```

#### 2. "TimeoutError ao carregar página"
- Verificar conexão internet
- Aumentar timeout nas configurações
- Site pode estar bloqueando requests

#### 3. "Dados não encontrados"
- Site pode ter mudado estrutura
- Verificar seletores CSS/XPath
- Executar em modo debug (headless=false)

#### 4. "Erro de importação"
```bash
# Verificar instalação das dependências
pip install -r requirements.txt
```

### Logs e Debugging

#### Habilitar Logs Detalhados
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Ver Logs da API
```bash
# Logs aparecem no terminal onde executou python run.py
```

#### Screenshots de Debug
```python
# Adicionar no scraper
await page.screenshot(path=f"debug_{datetime.now()}.png")
```

### Performance

#### Otimizar Scraping
- Reduzir `rate_limit` se o site permitir
- Usar `max_concurrent` adequado (2-3 é bom)
- Filtrar dados desnecessários no CSS selector

#### Monitorar Recursos
```bash
# Verificar uso de memória
curl http://localhost:8000/stats
```

## 🔗 Integração Radar-Infra

O **radar-webscrapping** é um dos 4 componentes do Sistema Radar e integra-se perfeitamente com o **radar-infra**:

### 🏗️ Arquitetura do Sistema Completo

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  radar-webapp   │    │ radar-webscrapping │    │  radar-webapi   │
│   (React)       │◄──►│    (Python)        │◄──►│  (Spring Boot)  │
│   Port: 3000    │    │    Port: 8000      │    │   Port: 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                         ┌─────────────────┐
                         │     MySQL       │
                         │   Port: 3306    │
                         └─────────────────┘
```

### 📋 Configuração no radar-infra

O **docker-compose.yml** do radar-infra já inclui a configuração completa:

```yaml
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

### 🔧 Variáveis de Ambiente (radar-infra)

Configure no `.env` do **radar-infra**:

```env
# Versão do WebScrapping  
WEBSCRAPPING_VERSION=latest
WEBSCRAPPING_PORT=8000

# Configurações de integração
RADAR_API_KEY=your-secure-api-key-here
SCRAPING_SCHEDULE=0 2 * * *  # Todo dia às 2h da manhã
SCRAPING_LOG_LEVEL=INFO

# URL da API para frontend
VITE_WEBSCRAPPING_URL=http://localhost:8000
```

### 🚀 Deploy Completo

```bash
# 1. Clone o radar-infra
git clone <radar-infra-repository>
cd radar-infra

# 2. Clone todos os sub-projetos
git clone <radar-webscrapping-repository>
git clone <radar-webapi-repository>  
git clone <radar-webapp-repository>

# 3. Configure .env
cp .env.example .env
# Edite conforme necessário

# 4. Execute todo o sistema
docker-compose up -d

# 5. Verifique status
docker-compose ps
```

### 📊 Monitoramento Integrado

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs apenas do webscrapping
docker-compose logs -f radar-webscrapping

# Health check do sistema
curl http://localhost:8080/actuator/health  # webapi
curl http://localhost:8000/health           # webscrapping
curl http://localhost:3000                  # webapp
```

### 🔄 Fluxo de Dados Integrado

1. **WebScrapping** coleta dados do SIGAA UFBA
2. **WebScrapping** envia dados para **WebAPI** via REST
3. **WebAPI** armazena no MySQL e processa
4. **WebApp** consome dados via **WebAPI**
5. **Usuários** acessam via **WebApp**

---

## 🎓 Desenvolvimento e Contribuição

### 🛠️ Setup para Desenvolvimento

```bash
# 1. Fork e clone
git clone <your-fork>
cd radar-webscrapping

# 2. Instalar dependências  
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Pre-commit hooks
pre-commit install

# 4. Executar testes
pytest tests/

# 5. Verificar cobertura
pytest --cov=src tests/
```

### 📚 Recursos de Aprendizado

- **Clean Architecture**: [Uncle Bob's Blog](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- **SOLID Principles**: [SOLID Principles Explained](https://en.wikipedia.org/wiki/SOLID)
- **Selenium Documentation**: [selenium-python.readthedocs.io](https://selenium-python.readthedocs.io/)
- **SQLAlchemy**: [docs.sqlalchemy.org](https://docs.sqlalchemy.org/)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)

### 🤝 Como Contribuir

1. **Issues**: Reporte bugs ou sugira melhorias
2. **Pull Requests**: Implemente funcionalidades seguindo Clean Architecture
3. **Documentação**: Melhore docs e exemplos
4. **Testes**: Adicione cobertura de testes
5. **Code Review**: Participe das revisões

---

**🎯 Sistema Radar - Recomendação Acadêmica UFBA**  
**Desenvolvido seguindo Clean Architecture e Princípios SOLID**  
**Versão 1.0 - 2024**