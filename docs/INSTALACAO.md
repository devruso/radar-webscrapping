# Guia de Instalação e Configuração

Este guia fornece instruções detalhadas para configurar o ambiente de desenvolvimento do projeto Radar Web Scraping.

## 📋 Pré-requisitos

### Sistema Operacional
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+)

### Software Necessário
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Editor de código** (recomendado: VS Code)

### Verificar Instalações
```bash
# Verificar Python
python --version
# Deve mostrar: Python 3.11.x ou superior

# Verificar pip
pip --version

# Verificar Git
git --version
```

## 🚀 Instalação Rápida

### Opção 1: Script Automático (Recomendado)

```bash
# 1. Clone o repositório
git clone <repository-url>
cd radar-webscrapping

# 2. Execute o setup automático
python setup.py
```

O script automático irá:
- ✅ Atualizar pip para versão mais recente
- ✅ Instalar todas as dependências Python
- ✅ Configurar navegadores Playwright
- ✅ Instalar dependências do sistema
- ✅ Verificar instalação

### Opção 2: Instalação Manual

Se preferir controle total sobre o processo:

```bash
# 1. Clone o repositório
git clone <repository-url>
cd radar-webscrapping

# 2. Criar ambiente virtual (recomendado)
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Atualizar pip
python -m pip install --upgrade pip

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Instalar navegadores Playwright
playwright install

# 7. Instalar dependências do sistema (opcional)
playwright install-deps
```

## ⚙️ Configuração

### 1. Arquivo de Ambiente

Copie o arquivo de exemplo e configure suas variáveis:

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
# Windows: notepad .env
# macOS/Linux: nano .env
```

### 2. Configurações Principais

Edite o arquivo `.env` com suas configurações:

```env
# ========================================
# CONFIGURAÇÕES DA API BACKEND
# ========================================
API_BASE_URL=http://localhost:8080/api
API_TIMEOUT=30
API_MAX_RETRIES=3

# ========================================
# CONFIGURAÇÕES DO BROWSER
# ========================================
# true = browser invisível (produção)
# false = browser visível (debug)
BROWSER_HEADLESS=true

# Delay entre requisições (em segundos)
BROWSER_RATE_LIMIT=1.0

# User agent para requisições
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# ========================================
# CONFIGURAÇÕES DE LOGGING
# ========================================
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log

# ========================================
# CONFIGURAÇÕES DE SCRAPING
# ========================================
# Máximo de scrapers executando simultaneamente
MAX_CONCURRENT_SCRAPERS=2

# Timeout para scraping (em segundos)
SCRAPING_TIMEOUT=300

# Tentativas de retry em caso de erro
RETRY_ATTEMPTS=3

# ========================================
# URLs DOS SITES UNIVERSITÁRIOS
# ========================================
# Configure conforme sua universidade
SITE_COURSES_URL=https://example-university.edu/courses
SITE_SCHEDULES_URL=https://example-university.edu/schedules
SITE_SYLLABI_URL=https://example-university.edu/syllabi

# ========================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO
# ========================================
DEBUG=true
RELOAD_ON_CHANGE=true
```

### 3. Configurações por Universidade

#### Universidade de Brasília (UnB)
```env
SITE_COURSES_URL=https://matriculaweb.unb.br/graduacao/oferta_dis.aspx
SITE_SCHEDULES_URL=https://matriculaweb.unb.br/graduacao/consulta_oferta.aspx
SITE_SYLLABI_URL=https://matriculaweb.unb.br/graduacao/ementas.aspx
```

#### USP
```env
SITE_COURSES_URL=https://uspdigital.usp.br/jupiterweb
SITE_SCHEDULES_URL=https://uspdigital.usp.br/jupiterweb/listarGradeCurricular
SITE_SYLLABI_URL=https://uspdigital.usp.br/jupiterweb/obterDisciplina
```

#### UNICAMP
```env
SITE_COURSES_URL=https://www.dac.unicamp.br/sistemas/catalogos/
SITE_SCHEDULES_URL=https://www.dac.unicamp.br/sistemas/horarios/
SITE_SYLLABI_URL=https://www.dac.unicamp.br/sistemas/ementas/
```

## 🔧 Configuração Avançada

### 1. Configurações de Proxy

Se sua instituição usa proxy:

```env
# Adicionar ao .env
HTTP_PROXY=http://proxy.university.edu:8080
HTTPS_PROXY=http://proxy.university.edu:8080
NO_PROXY=localhost,127.0.0.1
```

### 2. Configurações de Banco de Dados

Para armazenamento local (opcional):

```env
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/radar_scraping

# SQLite (mais simples)
DATABASE_URL=sqlite:///./radar_data.db

# MongoDB
MONGODB_URL=mongodb://localhost:27017/radar_scraping
```

### 3. Configurações de Redis (Cache)

Para cache avançado:

```env
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600  # 1 hora
```

## 🏃‍♂️ Executar o Sistema

### 1. Iniciar API em Desenvolvimento

```bash
# Método 1: Script de inicialização
python run.py

# Método 2: Diretamente
uvicorn src.main:app --reload --host localhost --port 8000
```

### 2. Verificar se Funcionou

Abra seu navegador e acesse:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Status**: http://localhost:8000/

Você deve ver:
```json
{
  "name": "Radar Web Scraping API",
  "version": "1.0.0",
  "status": "running",
  "available_scrapers": ["courses", "schedules", "syllabus"]
}
```

## 🧪 Testar Instalação

### 1. Teste Básico via API

```bash
# Testar health check
curl http://localhost:8000/health

# Listar scrapers disponíveis
curl http://localhost:8000/scrapers

# Executar scraping de teste
curl -X POST http://localhost:8000/scraping/start \
  -H "Content-Type: application/json" \
  -d '{
    "scraping_type": "courses",
    "config": {"max_pages": 1},
    "send_to_backend": false
  }'
```

### 2. Teste via Interface Web

1. Acesse http://localhost:8000/docs
2. Expanda o endpoint `POST /scraping/start`
3. Clique em "Try it out"
4. Modifique o JSON:
```json
{
  "scraping_type": "courses",
  "config": {
    "max_pages": 2
  },
  "send_to_backend": false
}
```
5. Clique "Execute"

### 3. Teste Programático

Crie um arquivo `test_scraping.py`:

```python
import asyncio
from src.scrapers.course_scraper import CourseScraper

async def test_scraper():
    scraper = CourseScraper()
    
    # Configuração de teste
    config = {
        'max_pages': 1,
        'debug': True
    }
    
    try:
        results = await scraper.scrape(config)
        print(f"✅ Teste bem-sucedido! {len(results)} cursos encontrados")
        
        for course in results[:3]:  # Mostrar apenas 3
            print(f"- {course.name} ({course.code})")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
```

Execute:
```bash
python test_scraping.py
```

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. "ModuleNotFoundError: No module named 'playwright'"

**Solução:**
```bash
# Verificar se está no ambiente virtual correto
pip list | grep playwright

# Se não estiver instalado:
pip install playwright
playwright install
```

#### 2. "playwright._impl._api_types.Error: Browser executable doesn't exist"

**Solução:**
```bash
# Reinstalar navegadores
playwright install --force

# Verificar instalação
playwright --version
```

#### 3. "TimeoutError: Timeout 30000ms exceeded"

**Causas possíveis:**
- Conexão lenta com internet
- Site universitário está lento/fora do ar
- Configurações de proxy

**Soluções:**
```env
# Aumentar timeout no .env
SCRAPING_TIMEOUT=600

# Ou desabilitar headless para debug
BROWSER_HEADLESS=false
```

#### 4. "Permission denied" no Linux/macOS

**Solução:**
```bash
# Dar permissões de execução
chmod +x setup.py
chmod +x run.py

# Ou executar com python diretamente
python setup.py
python run.py
```

#### 5. Erro de SSL/Certificados

**Solução:**
```env
# Adicionar ao .env para desenvolvimento
PYTHONHTTPSVERIFY=0
```

Ou instalar certificados:
```bash
# macOS
/Applications/Python\ 3.11/Install\ Certificates.command

# Linux
sudo apt-get update && sudo apt-get install ca-certificates
```

### Logs e Debugging

#### 1. Verificar Logs

```bash
# Ver logs da aplicação
tail -f logs/scraper.log

# Ver logs do sistema
# Windows: Event Viewer
# Linux: journalctl -f
# macOS: Console.app
```

#### 2. Executar em Modo Debug

```bash
# Definir nível de log
export LOG_LEVEL=DEBUG

# Executar com browser visível
export BROWSER_HEADLESS=false

python run.py
```

#### 3. Testar Conectividade

```python
# test_connectivity.py
import asyncio
import aiohttp

async def test_urls():
    urls = [
        "https://example-university.edu/courses",
        "http://localhost:8080/api/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"✅ {url}: {response.status}")
            except Exception as e:
                print(f"❌ {url}: {e}")

asyncio.run(test_urls())
```

### Performance

#### 1. Otimizar para Máquina Local

```env
# Para máquinas com pouca RAM
MAX_CONCURRENT_SCRAPERS=1
BROWSER_HEADLESS=true

# Para máquinas potentes
MAX_CONCURRENT_SCRAPERS=4
```

#### 2. Monitorar Recursos

```bash
# Ver uso de CPU/memória
top
# ou
htop

# Ver processos Python
ps aux | grep python
```

## 🐳 Docker (Opcional)

Para um ambiente completamente isolado:

### 1. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. docker-compose.yml

```yml
version: '3.8'

services:
  scraper:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BROWSER_HEADLESS=true
      - API_BASE_URL=http://backend:8080/api
    volumes:
      - ./logs:/app/logs
      - ./.env:/app/.env
    depends_on:
      - backend

  backend:
    image: your-backend-image
    ports:
      - "8080:8080"
```

### 3. Executar com Docker

```bash
# Build e executar
docker-compose up --build

# Apenas executar
docker-compose up

# Em background
docker-compose up -d
```

---

## ✅ Checklist Final

Antes de começar a usar o sistema, verifique:

- [ ] Python 3.11+ instalado e funcionando
- [ ] Dependências instaladas (`pip list` mostra todas)
- [ ] Navegadores Playwright configurados
- [ ] Arquivo `.env` configurado com suas URLs
- [ ] API iniciando sem erros (`python run.py`)
- [ ] Health check retornando sucesso (`curl localhost:8000/health`)
- [ ] Teste básico de scraping funcionando

## 📞 Suporte

Se encontrar problemas:

1. **Verifique os logs**: `logs/scraper.log`
2. **Consulte troubleshooting** acima
3. **Teste conectividade** com sites universitários
4. **Abra issue** no repositório com:
   - Sistema operacional
   - Versão do Python
   - Logs de erro completos
   - Passos para reproduzir

---

**Configuração concluída! 🎉 Agora você pode começar a usar o sistema de scraping.**