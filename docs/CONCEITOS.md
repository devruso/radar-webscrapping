# Conceitos de Web Scraping - Tutorial Educacional

Este documento explica os conceitos fundamentais de web scraping implementados no projeto Radar, servindo como guia educacional para desenvolvimento independente.

## 📚 Índice

1. [Introdução ao Web Scraping](#introdução-ao-web-scraping)
2. [Tipos de Scraping](#tipos-de-scraping)
3. [Ferramentas e Bibliotecas](#ferramentas-e-bibliotecas)
4. [Padrões de Design](#padrões-de-design)
5. [Técnicas Avançadas](#técnicas-avançadas)
6. [Boas Práticas](#boas-práticas)
7. [Casos de Uso Acadêmicos](#casos-de-uso-acadêmicos)

## 🌐 Introdução ao Web Scraping

### O que é Web Scraping?

Web scraping é o processo automatizado de extração de dados de websites. É como ter um assistente que visita páginas web, lê o conteúdo e organiza as informações em um formato estruturado.

### Por que é Importante?

1. **Automação**: Coleta dados 24/7 sem intervenção manual
2. **Escala**: Processa milhares de páginas rapidamente
3. **Consistência**: Dados sempre no mesmo formato
4. **Atualização**: Mantém informações sempre atualizadas

### Desafios Comuns

- **Sites Dinâmicos**: Conteúdo carregado via JavaScript
- **Anti-Bot**: Sistemas de proteção contra automação
- **Mudanças de Estrutura**: Sites que alteram o layout
- **Performance**: Balance entre velocidade e estabilidade

## 🔧 Tipos de Scraping

### 1. Scraping Estático (HTML Parser)

**Quando usar**: Sites com conteúdo estático, carregado diretamente no HTML.

```python
import requests
from bs4 import BeautifulSoup

def scrape_static_content(url):
    """
    Exemplo básico de scraping estático
    """
    # Fazer requisição HTTP
    response = requests.get(url)
    response.raise_for_status()  # Verificar se sucesso
    
    # Parsear HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extrair dados usando seletores CSS
    titles = soup.select('h2.course-title')
    
    courses = []
    for title in titles:
        course_name = title.get_text(strip=True)
        courses.append(course_name)
    
    return courses

# Uso
courses = scrape_static_content('https://university.edu/courses')
```

**Vantagens**:
- ✅ Rápido e eficiente
- ✅ Baixo uso de recursos
- ✅ Simples de implementar

**Desvantagens**:
- ❌ Não funciona com JavaScript
- ❌ Limitado a conteúdo estático

### 2. Scraping Dinâmico (Browser Automation)

**Quando usar**: Sites que dependem de JavaScript, SPAs, conteúdo carregado via AJAX.

```python
from playwright.async_api import async_playwright

async def scrape_dynamic_content(url):
    """
    Exemplo de scraping dinâmico com Playwright
    """
    async with async_playwright() as p:
        # Iniciar browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navegar para página
        await page.goto(url)
        
        # Aguardar conteúdo JavaScript carregar
        await page.wait_for_selector('.dynamic-course-list')
        
        # Extrair dados após JavaScript executar
        courses = await page.evaluate('''
            () => {
                const elements = document.querySelectorAll('.course-item');
                return Array.from(elements).map(el => ({
                    name: el.querySelector('.course-name').textContent,
                    code: el.querySelector('.course-code').textContent
                }));
            }
        ''')
        
        await browser.close()
        return courses

# Uso
courses = await scrape_dynamic_content('https://spa-university.edu/courses')
```

**Vantagens**:
- ✅ Funciona com JavaScript
- ✅ Simula comportamento real do usuário
- ✅ Pode interagir com elementos (cliques, formulários)

**Desvantagens**:
- ❌ Mais lento
- ❌ Usa mais recursos (CPU, memória)
- ❌ Mais complexo de configurar

### 3. Scraping Híbrido

**Quando usar**: Sites que têm partes estáticas e dinâmicas.

```python
async def hybrid_scraping(base_url):
    """
    Combina ambas as abordagens
    """
    # 1. Usar requests para páginas de índice (estático)
    response = requests.get(f"{base_url}/course-list")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extrair links para páginas dinâmicas
    course_links = [link['href'] for link in soup.select('a.course-link')]
    
    # 2. Usar Playwright para páginas dinâmicas
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        courses = []
        for link in course_links:
            page = await browser.new_page()
            await page.goto(link)
            
            # Aguardar dados dinâmicos
            await page.wait_for_selector('.course-details')
            
            # Extrair dados detalhados
            course_data = await page.evaluate('...')
            courses.append(course_data)
            
            await page.close()
        
        await browser.close()
    
    return courses
```

## 🛠️ Ferramentas e Bibliotecas

### Requisições HTTP

#### requests
```python
import requests

# GET simples
response = requests.get(url)

# POST com dados
response = requests.post(url, data={'key': 'value'})

# Headers customizados
headers = {'User-Agent': 'My Scraper 1.0'}
response = requests.get(url, headers=headers)

# Session para cookies persistentes
session = requests.Session()
session.get('https://site.com/login')
session.post('https://site.com/auth', data=login_data)
session.get('https://site.com/protected')  # Mantém cookies
```

#### httpx (async)
```python
import httpx

async def async_requests():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Parsing HTML

#### BeautifulSoup
```python
from bs4 import BeautifulSoup

# Diferentes parsers
soup = BeautifulSoup(html, 'html.parser')  # Built-in Python
soup = BeautifulSoup(html, 'lxml')         # Mais rápido
soup = BeautifulSoup(html, 'html5lib')     # Mais preciso

# Métodos de busca
soup.find('div', class_='content')         # Primeiro elemento
soup.find_all('a', href=True)             # Todos os links
soup.select('div.course-item')             # Seletor CSS
soup.select_one('#main-content')          # CSS, apenas primeiro

# Extração de dados
element.get_text()                         # Texto apenas
element.get_text(strip=True)              # Texto sem espaços
element['href']                           # Atributo
element.get('data-id', 'default')         # Atributo com default
```

#### lxml
```python
from lxml import html

# XPath support
tree = html.fromstring(page_content)
titles = tree.xpath('//h2[@class="course-title"]/text()')
```

### Browser Automation

#### Playwright
```python
from playwright.async_api import async_playwright

async def advanced_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Ver browser (debug)
            slow_mo=1000     # Delay entre ações
        )
        
        # Contexto com configurações
        context = await browser.new_context(
            user_agent='Custom Agent',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # Interceptar requests
        await page.route('**/*.png', lambda route: route.abort())
        
        # Navegar e aguardar
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Interações
        await page.click('button#load-more')
        await page.fill('input[name="search"]', 'computer science')
        await page.press('input[name="search"]', 'Enter')
        
        # Screenshots
        await page.screenshot(path='page.png')
        
        await browser.close()
```

#### Selenium (alternativa)
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get(url)

# Aguardar elemento aparecer
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.ID, "content")))

driver.quit()
```

### Processamento de Dados

#### Pydantic (Validação)
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class Course(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., regex=r'^[A-Z]{2,4}\d{3,4}$')
    credits: int = Field(..., ge=1, le=10)
    prerequisites: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.title()
    
    class Config:
        # Exemplo de uso
        schema_extra = {
            "example": {
                "name": "Data Structures",
                "code": "CS101",
                "credits": 3,
                "prerequisites": ["CS100"]
            }
        }

# Validação automática
try:
    course = Course(name="algorithms", code="CS102", credits=4)
    print(course.name)  # "Algorithms" (title case aplicado)
except ValidationError as e:
    print(e.json())
```

## 🏗️ Padrões de Design

### 1. Strategy Pattern

Diferentes estratégias de extração para diferentes tipos de sites:

```python
from abc import ABC, abstractmethod

class ExtractionStrategy(ABC):
    @abstractmethod
    async def extract(self, page) -> List[dict]:
        pass

class TableExtractionStrategy(ExtractionStrategy):
    async def extract(self, page) -> List[dict]:
        # Estratégia para dados em tabelas
        rows = await page.query_selector_all('table tr')
        data = []
        for row in rows[1:]:  # Skip header
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                data.append({
                    'name': await cells[0].inner_text(),
                    'code': await cells[1].inner_text(),
                    'credits': await cells[2].inner_text()
                })
        return data

class CardExtractionStrategy(ExtractionStrategy):
    async def extract(self, page) -> List[dict]:
        # Estratégia para dados em cards
        cards = await page.query_selector_all('.course-card')
        data = []
        for card in cards:
            name = await card.query_selector('.course-name')
            code = await card.query_selector('.course-code')
            data.append({
                'name': await name.inner_text() if name else '',
                'code': await code.inner_text() if code else ''
            })
        return data

class CourseExtractor:
    def __init__(self, strategy: ExtractionStrategy):
        self.strategy = strategy
    
    async def extract_courses(self, page):
        return await self.strategy.extract(page)

# Uso
if site_has_tables:
    extractor = CourseExtractor(TableExtractionStrategy())
else:
    extractor = CourseExtractor(CardExtractionStrategy())

courses = await extractor.extract_courses(page)
```

### 2. Factory Pattern

Criação dinâmica de scrapers baseado no tipo de site:

```python
from enum import Enum

class SiteType(Enum):
    UNIVERSITY_A = "university_a"
    UNIVERSITY_B = "university_b"
    GENERIC = "generic"

class ScraperFactory:
    _scrapers = {}
    
    @classmethod
    def register_scraper(cls, site_type: SiteType, scraper_class):
        cls._scrapers[site_type] = scraper_class
    
    @classmethod
    def create_scraper(cls, site_type: SiteType):
        scraper_class = cls._scrapers.get(site_type)
        if not scraper_class:
            raise ValueError(f"No scraper registered for {site_type}")
        return scraper_class()

# Registro
ScraperFactory.register_scraper(SiteType.UNIVERSITY_A, UniversityAScraper)
ScraperFactory.register_scraper(SiteType.UNIVERSITY_B, UniversityBScraper)

# Uso
scraper = ScraperFactory.create_scraper(SiteType.UNIVERSITY_A)
data = await scraper.scrape()
```

### 3. Template Method Pattern

Base comum com passos específicos customizáveis:

```python
class BaseScraper(ABC):
    async def scrape(self) -> List[dict]:
        """Template method - define o fluxo geral"""
        await self.setup()
        
        raw_data = await self.extract_raw_data()
        cleaned_data = await self.clean_data(raw_data)
        validated_data = await self.validate_data(cleaned_data)
        
        await self.cleanup()
        return validated_data
    
    @abstractmethod
    async def extract_raw_data(self) -> List[dict]:
        """Cada scraper implementa sua extração específica"""
        pass
    
    async def setup(self):
        """Setup padrão - pode ser sobrescrito"""
        self.page = await browser_manager.get_page()
    
    async def clean_data(self, data: List[dict]) -> List[dict]:
        """Limpeza padrão - pode ser sobrescrito"""
        cleaned = []
        for item in data:
            # Remover espaços, normalizar
            clean_item = {k: v.strip() if isinstance(v, str) else v 
                         for k, v in item.items()}
            cleaned.append(clean_item)
        return cleaned
    
    async def validate_data(self, data: List[dict]) -> List[dict]:
        """Validação padrão"""
        valid_data = []
        for item in data:
            try:
                # Usar Pydantic para validação
                validated_item = self.data_model(**item)
                valid_data.append(validated_item)
            except ValidationError:
                logger.warning(f"Invalid data: {item}")
        return valid_data
    
    async def cleanup(self):
        """Cleanup padrão"""
        if hasattr(self, 'page'):
            await self.page.close()

class CourseScraper(BaseScraper):
    data_model = Course  # Modelo Pydantic
    
    async def extract_raw_data(self) -> List[dict]:
        await self.page.goto('https://university.edu/courses')
        
        courses = []
        elements = await self.page.query_selector_all('.course-item')
        
        for element in elements:
            name = await element.query_selector('.name')
            code = await element.query_selector('.code')
            
            courses.append({
                'name': await name.inner_text() if name else '',
                'code': await code.inner_text() if code else ''
            })
        
        return courses
```

### 4. Observer Pattern

Monitoramento de progresso e eventos:

```python
class ScrapingObserver(ABC):
    @abstractmethod
    def on_progress(self, current: int, total: int, message: str):
        pass
    
    @abstractmethod
    def on_error(self, error: Exception):
        pass
    
    @abstractmethod
    def on_complete(self, results: List[dict]):
        pass

class ConsoleObserver(ScrapingObserver):
    def on_progress(self, current: int, total: int, message: str):
        percentage = (current / total) * 100
        print(f"Progress: {percentage:.1f}% - {message}")
    
    def on_error(self, error: Exception):
        print(f"Error: {error}")
    
    def on_complete(self, results: List[dict]):
        print(f"Completed! {len(results)} items scraped")

class ObservableScraper(BaseScraper):
    def __init__(self):
        self.observers: List[ScrapingObserver] = []
    
    def add_observer(self, observer: ScrapingObserver):
        self.observers.append(observer)
    
    def notify_progress(self, current: int, total: int, message: str):
        for observer in self.observers:
            observer.on_progress(current, total, message)
    
    def notify_error(self, error: Exception):
        for observer in self.observers:
            observer.on_error(error)
```

## 🚀 Técnicas Avançadas

### 1. Anti-Detecção

#### User Agent Rotation
```python
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Uso com requests
headers = {'User-Agent': get_random_user_agent()}
response = requests.get(url, headers=headers)

# Uso com Playwright
await page.set_extra_http_headers({'User-Agent': get_random_user_agent()})
```

#### Headers Realistas
```python
def get_realistic_headers():
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'utf-8',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }
```

#### Delays Aleatórios
```python
import asyncio
import random

async def human_like_delay():
    """Simula padrão humano de navegação"""
    delay = random.uniform(1, 3)  # 1-3 segundos
    await asyncio.sleep(delay)

async def random_scroll(page):
    """Scroll aleatório para simular leitura"""
    for _ in range(random.randint(2, 5)):
        await page.mouse.wheel(0, random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 2))
```

#### Stealth Mode
```python
# Com Playwright
async def setup_stealth_page(browser):
    context = await browser.new_context(
        user_agent=get_random_user_agent(),
        viewport={'width': 1366, 'height': 768},
        locale='pt-BR',
        timezone_id='America/Sao_Paulo'
    )
    
    page = await context.new_page()
    
    # Remover sinais de automação
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        window.chrome = {
            runtime: {},
        };
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
    """)
    
    return page
```

### 2. Rate Limiting Inteligente

```python
import time
from collections import deque

class AdaptiveRateLimiter:
    def __init__(self, initial_delay=1.0, max_delay=10.0):
        self.current_delay = initial_delay
        self.max_delay = max_delay
        self.success_times = deque(maxlen=10)
        self.error_count = 0
    
    async def wait(self):
        await asyncio.sleep(self.current_delay)
    
    def on_success(self):
        self.success_times.append(time.time())
        self.error_count = 0
        
        # Se muitos sucessos recentes, diminuir delay
        if len(self.success_times) >= 5:
            recent_successes = sum(1 for t in self.success_times 
                                 if time.time() - t < 60)
            if recent_successes >= 5:
                self.current_delay = max(0.5, self.current_delay * 0.9)
    
    def on_error(self):
        self.error_count += 1
        # Aumentar delay exponencialmente
        self.current_delay = min(self.max_delay, 
                               self.current_delay * (1.5 ** self.error_count))

# Uso
rate_limiter = AdaptiveRateLimiter()

async def scrape_with_rate_limiting(urls):
    for url in urls:
        try:
            await rate_limiter.wait()
            data = await scrape_page(url)
            rate_limiter.on_success()
            yield data
        except Exception as e:
            rate_limiter.on_error()
            logger.error(f"Error scraping {url}: {e}")
```

### 3. Retry Logic Robusto

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ScrapingError(Exception):
    pass

class TemporaryError(ScrapingError):
    """Erro temporário que vale a pena tentar novamente"""
    pass

class PermanentError(ScrapingError):
    """Erro permanente - não tentar novamente"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TemporaryError)
)
async def robust_scrape(url):
    try:
        page = await browser_manager.get_page()
        await page.goto(url, timeout=30000)
        
        # Verificar se página carregou corretamente
        if await page.locator('.error-404').count() > 0:
            raise PermanentError(f"Page not found: {url}")
        
        if await page.locator('.rate-limit').count() > 0:
            raise TemporaryError("Rate limited - will retry")
        
        # Extrair dados
        data = await extract_data(page)
        
        if not data:
            raise TemporaryError("No data found - might be temporary")
        
        return data
        
    except PlaywrightTimeoutError:
        raise TemporaryError("Timeout - will retry")
    except Exception as e:
        # Decidir se é erro temporário ou permanente
        if "connection" in str(e).lower():
            raise TemporaryError(f"Connection error: {e}")
        else:
            raise PermanentError(f"Permanent error: {e}")
```

### 4. Paralelização Controlada

```python
import asyncio
from asyncio import Semaphore

async def parallel_scraping(urls, max_concurrent=3):
    """
    Scraping paralelo com controle de concorrência
    """
    semaphore = Semaphore(max_concurrent)
    
    async def scrape_single(url):
        async with semaphore:  # Limita concorrência
            try:
                return await robust_scrape(url)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                return None
    
    # Criar tasks para todas as URLs
    tasks = [scrape_single(url) for url in urls]
    
    # Executar com progresso
    results = []
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        result = await coro
        if result:
            results.append(result)
        
        # Log de progresso
        logger.info(f"Progress: {i+1}/{len(urls)} completed")
    
    return results

# Uso
urls = ['https://site.com/page1', 'https://site.com/page2', ...]
results = await parallel_scraping(urls, max_concurrent=2)
```

### 5. Processamento de PDFs Avançado

```python
import fitz  # PyMuPDF
import pdfplumber
from typing import Tuple

class AdvancedPDFProcessor:
    async def extract_with_confidence(self, pdf_path: str) -> Tuple[str, float]:
        """
        Extrai texto de PDF com score de confiança
        """
        # Método 1: pdfplumber
        plumber_text = self._extract_with_pdfplumber(pdf_path)
        plumber_score = self._calculate_text_quality(plumber_text)
        
        # Método 2: PyMuPDF
        pymupdf_text = self._extract_with_pymupdf(pdf_path)
        pymupdf_score = self._calculate_text_quality(pymupdf_text)
        
        # Escolher melhor resultado
        if plumber_score > pymupdf_score:
            return plumber_text, plumber_score
        else:
            return pymupdf_text, pymupdf_score
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.error(f"pdfplumber error: {e}")
            return ""
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF error: {e}")
            return ""
    
    def _calculate_text_quality(self, text: str) -> float:
        """
        Calcula score de qualidade do texto extraído
        """
        if not text:
            return 0.0
        
        score = 0.0
        
        # Pontos por tamanho razoável
        if 100 < len(text) < 50000:
            score += 0.3
        
        # Pontos por caracteres válidos
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace())
        char_ratio = valid_chars / len(text)
        score += char_ratio * 0.4
        
        # Pontos por palavras completas
        words = text.split()
        complete_words = sum(1 for word in words if len(word) > 1 and word.isalpha())
        if words:
            word_ratio = complete_words / len(words)
            score += word_ratio * 0.3
        
        return min(score, 1.0)

# Uso
processor = AdvancedPDFProcessor()
text, confidence = await processor.extract_with_confidence("syllabus.pdf")

if confidence > 0.7:
    logger.info(f"High quality extraction (confidence: {confidence:.2f})")
    # Processar texto
else:
    logger.warning(f"Low quality extraction (confidence: {confidence:.2f})")
    # Talvez tentar OCR
```

## ✅ Boas Práticas

### 1. Estrutura de Código

```python
# ✅ BOM: Separação de responsabilidades
class CourseDataExtractor:
    """Responsável apenas pela extração"""
    async def extract_from_page(self, page) -> List[dict]:
        pass

class CourseDataValidator:
    """Responsável apenas pela validação"""
    def validate(self, data: List[dict]) -> List[Course]:
        pass

class CourseDataStorage:
    """Responsável apenas pelo armazenamento"""
    async def save(self, courses: List[Course]):
        pass

# ❌ RUIM: Classe faz tudo
class CourseProcessor:
    async def do_everything(self, url):
        # Extração, validação, armazenamento tudo junto
        pass
```

### 2. Tratamento de Erros

```python
# ✅ BOM: Erros específicos e informativos
class ScrapingError(Exception):
    """Base para erros de scraping"""
    pass

class PageNotFoundError(ScrapingError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Page not found: {url}")

class DataExtractionError(ScrapingError):
    def __init__(self, selector: str, page_url: str):
        self.selector = selector
        self.page_url = page_url
        super().__init__(f"Could not extract data with selector '{selector}' from {page_url}")

# Uso
try:
    data = await extract_course_data(page, '.course-item')
except DataExtractionError as e:
    logger.error(f"Extraction failed: {e}")
    # Tentar seletor alternativo
    data = await extract_course_data(page, '.course-card')
```

### 3. Logging Estruturado

```python
from loguru import logger
import json

# ✅ BOM: Logs estruturados com contexto
logger.add("scraping.log", format="{time} | {level} | {message} | {extra}")

async def scrape_with_logging(url: str):
    with logger.contextualize(
        url=url,
        scraper="CourseScraper",
        session_id=generate_session_id()
    ):
        logger.info("Starting scrape")
        
        try:
            data = await extract_data(url)
            logger.info("Scrape successful", extra={"items_found": len(data)})
            return data
            
        except Exception as e:
            logger.error("Scrape failed", extra={"error": str(e), "error_type": type(e).__name__})
            raise
```

### 4. Configuração Externa

```python
# ✅ BOM: Configurações externalizadas
from pydantic import BaseSettings

class ScrapingSettings(BaseSettings):
    max_concurrent_requests: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    rate_limit_delay: float = 1.0
    user_agent: str = "Academic Scraper 1.0"
    
    # Carregar de .env automaticamente
    class Config:
        env_file = ".env"

settings = ScrapingSettings()

# ❌ RUIM: Configurações hardcoded
MAX_REQUESTS = 5  # Não configurável
TIMEOUT = 30      # Não configurável
```

### 5. Testes

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
async def mock_page():
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[
        MagicMock(inner_text=AsyncMock(return_value="Course 1")),
        MagicMock(inner_text=AsyncMock(return_value="Course 2"))
    ])
    return page

@pytest.mark.asyncio
async def test_course_extraction(mock_page):
    extractor = CourseDataExtractor()
    
    # Teste com dados mocados
    result = await extractor.extract_from_page(mock_page)
    
    assert len(result) == 2
    assert result[0]['name'] == "Course 1"
    
    # Verificar se métodos foram chamados
    mock_page.goto.assert_called_once()
    mock_page.query_selector_all.assert_called_once()

# Teste de integração (mais lento)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_scraping():
    scraper = CourseScraper()
    results = await scraper.scrape("https://test-university.edu/courses")
    
    assert len(results) > 0
    assert all(isinstance(r, Course) for r in results)
```

## 🎓 Casos de Uso Acadêmicos

### 1. Sistema de Recomendação de Disciplinas

```python
class CourseRecommendationScraper:
    """
    Coleta dados para sistema de recomendação
    """
    async def scrape_comprehensive_data(self):
        # Disciplinas disponíveis
        courses = await self.scrape_courses()
        
        # Pré-requisitos e dependências
        prerequisites = await self.scrape_prerequisites()
        
        # Avaliações de professores
        ratings = await self.scrape_professor_ratings()
        
        # Horários e conflitos
        schedules = await self.scrape_schedules()
        
        # Ementas e conteúdo
        syllabi = await self.scrape_syllabi()
        
        return {
            'courses': courses,
            'prerequisites': prerequisites,
            'ratings': ratings,
            'schedules': schedules,
            'syllabi': syllabi
        }
```

### 2. Monitoramento de Vagas

```python
class EnrollmentMonitorScraper:
    """
    Monitora vagas disponíveis em disciplinas
    """
    async def monitor_enrollment(self, course_codes: List[str]):
        while True:
            for code in course_codes:
                availability = await self.check_availability(code)
                
                if availability['spots_available'] > 0:
                    await self.notify_user(code, availability)
                
                await asyncio.sleep(300)  # Check every 5 minutes
    
    async def check_availability(self, course_code: str) -> dict:
        page = await browser_manager.get_page()
        await page.goto(f"https://university.edu/enrollment/{course_code}")
        
        spots_element = await page.query_selector('.spots-available')
        spots_text = await spots_element.inner_text()
        
        # Extrair número usando regex
        match = re.search(r'(\d+)', spots_text)
        spots_available = int(match.group(1)) if match else 0
        
        return {
            'course_code': course_code,
            'spots_available': spots_available,
            'last_checked': datetime.now()
        }
```

### 3. Análise de Grade Curricular

```python
class CurriculumAnalysisScraper:
    """
    Analisa estrutura de cursos e grades curriculares
    """
    async def analyze_curriculum(self, program_id: str):
        # Disciplinas obrigatórias
        required_courses = await self.scrape_required_courses(program_id)
        
        # Disciplinas optativas
        elective_courses = await self.scrape_elective_courses(program_id)
        
        # Trilhas/especializações
        tracks = await self.scrape_specialization_tracks(program_id)
        
        # Análise de dependências
        dependency_graph = self.build_dependency_graph(required_courses)
        
        return {
            'program_id': program_id,
            'required_courses': required_courses,
            'elective_courses': elective_courses,
            'tracks': tracks,
            'dependency_graph': dependency_graph,
            'total_credits': sum(c['credits'] for c in required_courses)
        }
    
    def build_dependency_graph(self, courses: List[dict]) -> dict:
        """
        Constrói grafo de dependências entre disciplinas
        """
        graph = {}
        
        for course in courses:
            code = course['code']
            prereqs = course.get('prerequisites', [])
            
            graph[code] = {
                'prerequisites': prereqs,
                'dependents': []
            }
        
        # Construir dependentes (direção oposta)
        for course_code, data in graph.items():
            for prereq in data['prerequisites']:
                if prereq in graph:
                    graph[prereq]['dependents'].append(course_code)
        
        return graph
```

### 4. Pesquisa Científica

```python
class ResearchDataScraper:
    """
    Coleta dados para pesquisas acadêmicas
    """
    async def scrape_research_data(self, research_topic: str):
        # Publicações recentes
        publications = await self.scrape_publications(research_topic)
        
        # Professores por área
        professors = await self.scrape_professors_by_area(research_topic)
        
        # Projetos de pesquisa
        projects = await self.scrape_research_projects(research_topic)
        
        # Estatísticas de citações
        citations = await self.scrape_citation_data(publications)
        
        return {
            'topic': research_topic,
            'publications': publications,
            'professors': professors,
            'projects': projects,
            'citations': citations
        }
```

## 📊 Métricas e Monitoramento

### Performance Tracking

```python
import time
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ScrapingMetrics:
    start_time: float
    end_time: float
    pages_scraped: int
    items_extracted: int
    errors: int
    average_page_time: float
    
    @property
    def total_time(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def items_per_second(self) -> float:
        return self.items_extracted / self.total_time if self.total_time > 0 else 0

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            'page_load_times': [],
            'extraction_times': [],
            'error_counts': []
        }
    
    def record_page_load(self, load_time: float):
        self.metrics['page_load_times'].append(load_time)
    
    def record_extraction(self, extraction_time: float):
        self.metrics['extraction_times'].append(extraction_time)
    
    def get_stats(self) -> dict:
        return {
            'avg_page_load': sum(self.metrics['page_load_times']) / len(self.metrics['page_load_times']),
            'avg_extraction': sum(self.metrics['extraction_times']) / len(self.metrics['extraction_times']),
            'total_errors': sum(self.metrics['error_counts'])
        }

# Uso com context manager
class TimedScraper:
    def __init__(self):
        self.metrics = MetricsCollector()
    
    async def scrape_with_timing(self, url: str):
        # Timing de carregamento
        start_load = time.time()
        await page.goto(url)
        load_time = time.time() - start_load
        self.metrics.record_page_load(load_time)
        
        # Timing de extração
        start_extraction = time.time()
        data = await self.extract_data(page)
        extraction_time = time.time() - start_extraction
        self.metrics.record_extraction(extraction_time)
        
        return data
```

## 🔧 Debugging Avançado

### Visual Debugging

```python
class VisualDebugger:
    def __init__(self, screenshot_dir: str = "debug_screenshots"):
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.step_counter = 0
    
    async def debug_step(self, page, description: str):
        """Captura screenshot e HTML em cada passo"""
        self.step_counter += 1
        
        # Screenshot
        screenshot_path = self.screenshot_dir / f"step_{self.step_counter:03d}_{description}.png"
        await page.screenshot(path=str(screenshot_path))
        
        # HTML source
        html_path = self.screenshot_dir / f"step_{self.step_counter:03d}_{description}.html"
        content = await page.content()
        html_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Debug step {self.step_counter}: {description}")
        logger.info(f"Screenshot: {screenshot_path}")
        logger.info(f"HTML: {html_path}")

# Uso
debugger = VisualDebugger()

async def debug_scraping():
    page = await browser_manager.get_page()
    
    await debugger.debug_step(page, "initial_page")
    await page.goto("https://university.edu/courses")
    
    await debugger.debug_step(page, "after_navigation")
    await page.click("#load-more-courses")
    
    await debugger.debug_step(page, "after_load_more")
    courses = await page.query_selector_all(".course-item")
    
    logger.info(f"Found {len(courses)} courses")
```

Este guia fornece uma base sólida para entender e implementar web scraping de forma independente. Pratique com sites simples primeiro, depois evolua para casos mais complexos conforme ganha experiência!

---

**Recursos Adicionais:**
- [Playwright Documentation](https://playwright.dev/python/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)