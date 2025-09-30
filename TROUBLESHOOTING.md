# 🚨 Troubleshooting - Radar WebScrapping

**Soluções para problemas comuns durante desenvolvimento**

## 📋 Índice

1. [Problemas de Ambiente](#problemas-de-ambiente)
2. [Problemas de Scraping](#problemas-de-scraping)
3. [Problemas de Docker](#problemas-de-docker)
4. [Problemas de GitHub Actions](#problemas-de-github-actions)
5. [Problemas de Testes](#problemas-de-testes)
6. [Problemas de Performance](#problemas-de-performance)
7. [Comandos de Emergência](#comandos-de-emergência)

---

## 🛠️ Problemas de Ambiente

### Problema 1: "Python não encontra módulos"

#### **Sintomas:**
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'CursoScraper'
```

#### **Diagnóstico:**
```bash
# Verificar se está no diretório certo
pwd
# Deve ser: /path/to/radar-webscrapping

# Verificar estrutura
ls -la src/
```

#### **Soluções:**

##### **Opção 1: PYTHONPATH**
```bash
# Temporário (só na sessão atual)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py

# Permanente (no .bashrc/.zshrc)
echo 'export PYTHONPATH="${PYTHONPATH}:/caminho/para/radar-webscrapping"' >> ~/.bashrc
```

##### **Opção 2: Instalação Editable**
```bash
# Instalar o projeto como pacote
pip install -e .

# Agora imports funcionam de qualquer lugar
python -c "from src.scrapers import CursoScraper; print('OK')"
```

##### **Opção 3: Docker (recomendado)**
```bash
# No Docker, tudo já está configurado
docker-compose exec webscrapping python main.py
```

### Problema 2: "Conflito de versões Python"

#### **Sintomas:**
```
ERROR: Package has invalid metadata
This package requires Python >=3.11
```

#### **Diagnóstico:**
```bash
# Verificar versão atual
python --version
python3 --version

# Verificar versões disponíveis
ls /usr/bin/python*
```

#### **Soluções:**

##### **Linux/Mac:**
```bash
# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv  # Ubuntu/Debian
brew install python@3.11                      # macOS

# Criar venv com versão específica
python3.11 -m venv venv
source venv/bin/activate
```

##### **Windows:**
```cmd
# Baixar do python.org ou usar Microsoft Store
# Ou via Chocolatey:
choco install python --version=3.11.0

# Criar venv
py -3.11 -m venv venv
venv\Scripts\activate
```

### Problema 3: "Permissões negadas"

#### **Sintomas:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages'
```

#### **Soluções:**
```bash
# NUNCA use sudo pip install!

# Opção 1: Virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Opção 2: User install
pip install --user -r requirements.txt

# Opção 3: Docker (sem problemas de permissão)
docker-compose up -d
```

---

## 🕷️ Problemas de Scraping

### Problema 1: "Selenium não encontra Chrome"

#### **Sintomas:**
```
selenium.common.exceptions.WebDriverException: 
Message: 'chromedriver' executable needs to be in PATH
```

#### **Diagnóstico:**
```bash
# Verificar se Chrome está instalado
google-chrome --version     # Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # Mac
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version  # Windows

# Verificar ChromeDriver
chromedriver --version
```

#### **Soluções:**

##### **Opção 1: Selenium Manager (automático)**
```python
# Selenium 4.6+ gerencia automaticamente
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Não precisa especificar caminho
driver = webdriver.Chrome()
```

##### **Opção 2: WebDriver Manager**
```bash
pip install webdriver-manager
```

```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

##### **Opção 3: Docker (recomendado)**
```bash
# No Docker, Chrome já está instalado e configurado
docker-compose exec webscrapping python -c "
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://google.com')
print('Chrome funcionando!')
driver.quit()
"
```

### Problema 2: "Timeout ao carregar página"

#### **Sintomas:**
```
TimeoutException: Message: timeout: Timed out receiving message from renderer
```

#### **Diagnóstico:**
```python
# Teste manual de conectividade
import requests
response = requests.get('https://sigaa.ufba.br', timeout=10)
print(f"Status: {response.status_code}")
print(f"Tempo: {response.elapsed.total_seconds()}s")
```

#### **Soluções:**

##### **Aumentar timeouts:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.set_page_load_timeout(60)  # Timeout de página
driver.implicitly_wait(30)        # Timeout de elementos

# Aguardar elemento específico
wait = WebDriverWait(driver, 30)
element = wait.until(EC.presence_of_element_located((By.ID, "elemento-id")))
```

##### **Configurar Chrome para sites lentos:**
```python
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-extensions')
options.add_argument('--disable-images')  # Não carregar imagens
options.add_argument('--disable-javascript')  # Se não precisar de JS

driver = webdriver.Chrome(options=options)
```

### Problema 3: "Elementos não encontrados"

#### **Sintomas:**
```
NoSuchElementException: Message: no such element: Unable to locate element
```

#### **Diagnóstico:**
```python
# Debug passo a passo
driver.get('https://sigaa.ufba.br')

# Verificar se página carregou
print("Título:", driver.title)
print("URL atual:", driver.current_url)

# Procurar elementos
elements = driver.find_elements(By.TAG_NAME, "a")
print(f"Links encontrados: {len(elements)}")

# Salvar HTML para análise
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)
```

#### **Soluções:**

##### **Aguardar elementos:**
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Aguardar elemento aparecer
wait = WebDriverWait(driver, 30)
element = wait.until(EC.presence_of_element_located((By.ID, "elemento-id")))

# Aguardar elemento ser clicável
element = wait.until(EC.element_to_be_clickable((By.ID, "botao-id")))
```

##### **Seletores mais robustos:**
```python
# Múltiplas estratégias
try:
    element = driver.find_element(By.ID, "elemento-id")
except NoSuchElementException:
    try:
        element = driver.find_element(By.CLASS_NAME, "elemento-class")
    except NoSuchElementException:
        element = driver.find_element(By.XPATH, "//div[@class='elemento-class']")
```

### Problema 4: "Site detecta bot"

#### **Sintomas:**
```
Access Denied
You don't have permission to access this resource
```

#### **Soluções:**

##### **User Agent humano:**
```python
options = Options()
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
```

##### **Stealth mode:**
```bash
pip install undetected-chromedriver
```

```python
import undetected_chromedriver as uc

driver = uc.Chrome()
driver.get('https://sigaa.ufba.br')
```

##### **Headers customizados:**
```python
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

---

## 🐳 Problemas de Docker

### Problema 1: "Container não sobe"

#### **Sintomas:**
```
docker-compose up
webscrapping exited with code 1
```

#### **Diagnóstico:**
```bash
# Ver logs detalhados
docker-compose logs webscrapping

# Executar comando diretamente
docker-compose run --rm webscrapping bash

# Dentro do container:
python main.py --help
```

#### **Soluções Comuns:**

##### **Variável de ambiente faltando:**
```bash
# Verificar .env
cat .env

# Comparar com .env.example
diff .env .env.example

# Adicionar variáveis faltantes
echo "SIGAA_BASE_URL=https://sigaa.ufba.br" >> .env
```

##### **Problema de permissões:**
```bash
# Verificar dono dos arquivos
ls -la

# Corrigir se necessário
sudo chown -R $USER:$USER .
```

##### **Porta em uso:**
```bash
# Verificar porta 8000
netstat -tulpn | grep 8000
lsof -i :8000

# Parar processo ou mudar porta no docker-compose.yml
```

### Problema 2: "Build do Docker falha"

#### **Sintomas:**
```
docker build -t radar/webscrapping .
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

#### **Diagnóstico:**
```dockerfile
# Adicionar debug no Dockerfile
RUN pip install -r requirements.txt -v
```

#### **Soluções:**

##### **Cache corrompido:**
```bash
# Build sem cache
docker build --no-cache -t radar/webscrapping .

# Limpar sistema Docker
docker system prune -f
docker builder prune -f
```

##### **Dependência problemática:**
```bash
# Teste no container base
docker run --rm -it python:3.11-slim bash
pip install -r requirements.txt

# Se falhar, identificar dependência e corrigir
```

### Problema 3: "Volume não sincroniza"

#### **Sintomas:**
- Alterações no código não aparecem no container
- Arquivos criados no container não aparecem no host

#### **Soluções:**
```yaml
# docker-compose.yml - verificar volumes
services:
  webscrapping:
    volumes:
      - ./src:/app/src                    # Código fonte
      - ./data:/app/data                  # Dados persistentes
      - ./logs:/app/logs                  # Logs
      # NO Windows, talvez precise de:
      - type: bind
        source: ./src
        target: /app/src
```

```bash
# Reiniciar com volumes limpos
docker-compose down -v
docker-compose up -d

# Verificar se volumes foram criados
docker volume ls
```

---

## 🤖 Problemas de GitHub Actions

### Problema 1: "CI falha mas funciona localmente"

#### **Sintomas:**
```
✅ Local: pytest tests/ → All tests pass
❌ CI: pytest tests/ → FAILED
```

#### **Diagnóstico:**
```bash
# Reproduzir ambiente CI localmente
docker run --rm -it python:3.11-slim bash
pip install -r requirements.txt
pytest tests/
```

#### **Soluções Comuns:**

##### **Dependências diferentes:**
```bash
# Pinar todas as dependências
pip freeze > requirements.txt
git add requirements.txt
git commit -m "fix: pinar versões de dependências"
```

##### **Timezone diferente:**
```python
# Usar UTC em testes
from datetime import datetime, timezone

def test_data():
    now = datetime.now(timezone.utc)  # Não datetime.now()
```

##### **Caminhos diferentes:**
```python
# Usar pathlib para compatibilidade
from pathlib import Path

# Não usar:
path = "src/data/test.txt"

# Usar:
path = Path(__file__).parent / "data" / "test.txt"
```

### Problema 2: "Workflow não executa"

#### **Sintomas:**
- Push para GitHub mas Actions não roda
- Workflow fica "queued" infinitamente

#### **Diagnóstico:**
```yaml
# Verificar trigger no workflow
on:
  push:
    branches: [ main, develop ]  # Sua branch está aqui?
  pull_request:
    branches: [ main ]
```

#### **Soluções:**
```bash
# 1. Verificar branch
git branch  # Você está na branch certa?

# 2. Verificar sintaxe YAML
yamllint .github/workflows/ci-cd.yml

# 3. Executar manualmente
gh workflow run ci-cd.yml

# 4. Verificar limites do GitHub
# GitHub → Settings → Actions → Usage
```

### Problema 3: "Workflow muito lento"

#### **Sintomas:**
- CI demora > 30 minutos
- Jobs fazem timeout

#### **Soluções:**

##### **Cache de dependências:**
```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

##### **Executar jobs em paralelo:**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    # Este job roda independente
    
  test:
    runs-on: ubuntu-latest
    # Este também roda em paralelo
    
  build:
    runs-on: ubuntu-latest
    needs: [lint, test]  # Só roda depois de lint e test
```

##### **Reduzir escopo de testes:**
```yaml
- name: Run tests
  run: |
    if [ "${{ github.event_name }}" == "pull_request" ]; then
      pytest tests/unit/  # Só unit tests em PR
    else
      pytest tests/       # Full suite no main
    fi
```

---

## 🧪 Problemas de Testes

### Problema 1: "Testes intermitentes"

#### **Sintomas:**
- Teste passa às vezes, falha outras
- "Flaky tests"

#### **Diagnóstico:**
```bash
# Executar teste múltiplas vezes
for i in {1..10}; do 
  echo "Execução $i"
  pytest tests/test_flaky.py::test_funcao
done
```

#### **Soluções:**

##### **Fixar dados randômicos:**
```python
import random
import pytest

@pytest.fixture(autouse=True)
def seed_random():
    random.seed(42)
    # Agora random.choice() sempre retorna o mesmo
```

##### **Mock de APIs externas:**
```python
import pytest
from unittest.mock import patch, Mock

@patch('requests.get')
def test_api_call(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {'data': 'test'}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Seu teste aqui
```

##### **Aguardar condições assíncronas:**
```python
import time
import pytest
from selenium.webdriver.support.ui import WebDriverWait

def test_elemento_aparece():
    driver.get("http://exemplo.com")
    
    # Não usar sleep!
    # time.sleep(5)  ❌
    
    # Usar WebDriverWait
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.ID, "elemento")))
```

### Problema 2: "Testes não cobrem casos reais"

#### **Sintomas:**
- Coverage alto mas bugs em produção
- Testes passam mas código não funciona

#### **Soluções:**

##### **Testes de integração:**
```python
def test_scraping_completo():
    """Teste real com SIGAA"""
    scraper = CursoScraper()
    cursos = scraper.buscar_cursos_por_unidade("IME")
    
    assert len(cursos) > 0
    assert all(curso.codigo for curso in cursos)
    assert all(curso.nome for curso in cursos)
```

##### **Testes com dados reais:**
```python
@pytest.mark.integration
def test_com_sigaa_real():
    """Marca como integração para executar separado"""
    # Teste com site real
    pass

# Executar: pytest -m integration
```

##### **Property-based testing:**
```bash
pip install hypothesis
```

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1), st.integers(min_value=1))
def test_funcao_com_dados_diversos(texto, numero):
    resultado = sua_funcao(texto, numero)
    assert isinstance(resultado, str)
```

---

## ⚡ Problemas de Performance

### Problema 1: "Scraping muito lento"

#### **Sintomas:**
- 1 curso demora > 10 segundos
- Timeout frequente

#### **Diagnóstico:**
```python
import time

def benchmark_scraping():
    start = time.time()
    
    scraper = CursoScraper()
    cursos = scraper.buscar_cursos_por_unidade("IME")
    
    end = time.time()
    
    print(f"Tempo total: {end-start:.2f}s")
    print(f"Cursos encontrados: {len(cursos)}")
    print(f"Tempo por curso: {(end-start)/len(cursos):.2f}s")
```

#### **Soluções:**

##### **Otimizar Selenium:**
```python
options = Options()
options.add_argument('--disable-images')          # Não carregar imagens
options.add_argument('--disable-javascript')      # Se não precisar
options.add_argument('--disable-css')             # Não carregar CSS
options.add_argument('--disable-plugins')
options.add_argument('--disable-extensions')

# Page load strategy
options.page_load_strategy = 'eager'  # Não aguardar tudo carregar
```

##### **Requests em vez de Selenium:**
```python
# Se possível, use requests (muito mais rápido)
import requests
from bs4 import BeautifulSoup

def scrape_with_requests():
    session = requests.Session()
    response = session.get('https://sigaa.ufba.br/...')
    soup = BeautifulSoup(response.content, 'html.parser')
    # Parse HTML com BeautifulSoup
```

##### **Processamento paralelo:**
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def scrape_curso_async(codigo):
    # Scraping assíncrono
    pass

async def scrape_multiplos_cursos(codigos):
    tasks = [scrape_curso_async(codigo) for codigo in codigos]
    resultados = await asyncio.gather(*tasks)
    return resultados
```

### Problema 2: "Alto uso de memória"

#### **Sintomas:**
- Container usa > 2GB RAM
- OOMKilled no Docker

#### **Diagnóstico:**
```bash
# Monitor de memória
docker stats webscrapping

# Profiling Python
pip install memory-profiler
```

```python
from memory_profiler import profile

@profile
def funcao_com_vazamento():
    # Seu código aqui
    pass

# Executar: python -m memory_profiler script.py
```

#### **Soluções:**

##### **Limpar recursos:**
```python
def scrape_cursos():
    driver = webdriver.Chrome()
    try:
        # Scraping aqui
        pass
    finally:
        driver.quit()  # SEMPRE fechar driver
        
# Ou usar context manager
from contextlib import contextmanager

@contextmanager
def get_driver():
    driver = webdriver.Chrome()
    try:
        yield driver
    finally:
        driver.quit()

# Uso:
with get_driver() as driver:
    driver.get("https://sigaa.ufba.br")
```

##### **Processar em lotes:**
```python
def scrape_em_lotes(cursos, batch_size=10):
    for i in range(0, len(cursos), batch_size):
        lote = cursos[i:i + batch_size]
        
        # Processar lote
        processar_lote(lote)
        
        # Limpar memória
        gc.collect()
```

---

## 🆘 Comandos de Emergência

### "Tudo quebrou! Socorro!"

#### **Reset Completo:**
```bash
# 1. Parar tudo
docker-compose down -v
docker system prune -f

# 2. Voltar para última versão funcional
git log --oneline -10  # Ver commits recentes
git reset --hard [hash-do-commit-bom]

# 3. Reconstruir do zero
docker-compose build --no-cache
docker-compose up -d

# 4. Testar
docker-compose exec webscrapping python main.py status
```

#### **Backup de Emergência:**
```bash
# Backup dos dados
docker-compose exec postgres pg_dump -U postgres radar_webscrapping > backup-$(date +%Y%m%d).sql

# Backup do código (antes de reset)
tar czf codigo-backup-$(date +%Y%m%d).tar.gz src/ tests/ *.py *.yml

# Backup de logs
docker-compose exec webscrapping tar czf /tmp/logs.tar.gz logs/
docker cp webscrapping_container:/tmp/logs.tar.gz ./logs-backup-$(date +%Y%m%d).tar.gz
```

#### **Restaurar Estado Funcional:**
```bash
# 1. Identificar última versão funcional
git log --grep="✅" --oneline -10  # Commits que passaram CI

# 2. Criar branch de emergência
git checkout -b emergencia-$(date +%Y%m%d)

# 3. Reset para versão funcional
git reset --hard [hash-funcional]

# 4. Testar imediatamente
docker-compose up -d
docker-compose exec webscrapping python main.py status

# 5. Se funcionar, fazer push
git push origin emergencia-$(date +%Y%m%d)
```

### Comandos de Debug Rápido:

```bash
# Status geral
docker-compose ps
docker-compose logs --tail=20 webscrapping

# Conectividade
docker-compose exec webscrapping curl -I https://sigaa.ufba.br

# Teste Python básico
docker-compose exec webscrapping python -c "import src; print('Import OK')"

# Teste Selenium básico
docker-compose exec webscrapping python -c "
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://google.com')
print('Selenium OK:', driver.title)
driver.quit()
"

# Espaço em disco
df -h
docker system df

# Processos em execução
docker-compose top
```

---

## 📞 Quando Pedir Ajuda

### Antes de pedir ajuda, colete:

#### **1. Informações do ambiente:**
```bash
# Sistema
uname -a                    # Linux/Mac
systeminfo                  # Windows

# Docker
docker --version
docker-compose --version

# Python
python --version
pip --version

# Git
git --version
git status
git log --oneline -5
```

#### **2. Logs completos:**
```bash
# Logs da aplicação
docker-compose logs webscrapping > logs-completos.txt

# Logs do sistema
journalctl -u docker > docker-system.log  # Linux

# Logs de erro específico
# Copie a mensagem de erro completa
```

#### **3. Passos para reproduzir:**
```bash
# Documente exatamente o que você fez:
# 1. Executei: docker-compose up
# 2. Acessei: http://localhost:8000
# 3. Cliquei em: ...
# 4. Erro apareceu: ...
```

### Onde pedir ajuda:

1. **GitHub Issues**: Para bugs do projeto
2. **Stack Overflow**: Para problemas técnicos gerais
3. **Docker Community**: Para problemas de containerização
4. **Selenium Docs**: Para problemas de web scraping

---

**🎯 Agora você tem ferramentas para resolver praticamente qualquer problema!**

**Lembre-se:**
- ✅ Sempre leia a mensagem de erro completa
- ✅ Google é seu amigo - copie/cole erros
- ✅ Docker resolve 90% dos problemas de ambiente
- ✅ Logs são sua melhor ferramenta de debug
- ✅ Quando tudo falhar, reset completo funciona

**Troubleshooting confiante! 🛠️**