"""
Configurações centralizadas para o sistema de web scraping.

Este módulo centraliza todas as configurações do sistema:
1. URLs dos sites a serem coletados
2. Configurações do navegador e rate limiting
3. Configurações da API backend
4. Configurações de logging e monitoramento
"""
import os
from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BrowserConfig:
    """Configurações do navegador Playwright"""
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    timeout: int = 30000  # 30 segundos
    rate_limit: float = 1.0  # Intervalo entre requisições (segundos)
    max_concurrent_pages: int = 5
    user_agent: str = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})


@dataclass
class ScrapingTargets:
    """URLs e configurações dos sites-alvo"""
    # URLs base dos sistemas acadêmicos (exemplos genéricos)
    university_portal: str = "https://portal.universidade.edu.br"
    course_catalog: str = "https://portal.universidade.edu.br/graduacao/disciplinas"
    schedule_system: str = "https://portal.universidade.edu.br/horarios"
    syllabus_repository: str = "https://portal.universidade.edu.br/ementas"
    professor_directory: str = "https://portal.universidade.edu.br/docentes"
    
    # Configurações específicas por site
    login_required: bool = False
    login_url: str = "https://portal.universidade.edu.br/login"
    
    # Seletores CSS comuns (devem ser ajustados para cada site específico)
    course_selectors: Dict[str, str] = field(default_factory=lambda: {
        "course_list": ".course-list .course-item",
        "course_code": ".course-code",
        "course_name": ".course-name",
        "credits": ".credits",
        "department": ".department"
    })
    
    schedule_selectors: Dict[str, str] = field(default_factory=lambda: {
        "schedule_table": ".schedule-table",
        "time_slot": ".time-slot",
        "course_info": ".course-info",
        "professor": ".professor-name"
    })


@dataclass
class APIConfig:
    """Configurações da API backend (radar-webapi)"""
    base_url: str = "http://localhost:8080"
    timeout: int = 30
    retry_attempts: int = 3
    
    # Endpoints específicos
    endpoints: Dict[str, str] = field(default_factory=lambda: {
        "courses": "/api/v1/courses",
        "schedules": "/api/v1/schedules", 
        "professors": "/api/v1/professors",
        "syllabi": "/api/v1/syllabi",
        "health": "/actuator/health"
    })
    
    # Headers padrão
    headers: Dict[str, str] = field(default_factory=lambda: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Radar-WebScraping/1.0"
    })


@dataclass
class LoggingConfig:
    """Configurações de logging"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    rotation: str = "1 day"
    retention: str = "7 days"
    compression: str = "zip"
    
    # Diretório de logs
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    
    # Arquivos de log específicos
    files: Dict[str, str] = field(default_factory=lambda: {
        "main": "radar_scraping.log",
        "errors": "errors.log",
        "performance": "performance.log"
    })


@dataclass
class PDFConfig:
    """Configurações para processamento de PDFs"""
    max_file_size_mb: int = 50
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    extraction_timeout: int = 60  # segundos
    
    # Configurações do pdfplumber
    pdfplumber_config: Dict[str, Any] = field(default_factory=lambda: {
        "laparams": {
            "line_margin": 0.5,
            "word_margin": 0.1,
            "char_margin": 2.0,
            "boxes_flow": 0.5
        }
    })


@dataclass
class SecurityConfig:
    """Configurações de segurança"""
    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    
    # User agents rotativos para evitar detecção
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ])
    
    # Proxies (se necessário)
    proxies: List[str] = field(default_factory=list)
    
    # Headers para evitar detecção
    stealth_headers: Dict[str, str] = field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })


class Config:
    """
    Classe principal de configuração que centraliza todas as configurações.
    
    Carrega configurações de:
    1. Variáveis de ambiente
    2. Arquivo .env
    3. Valores padrão
    """
    
    def __init__(self):
        self.browser = BrowserConfig()
        self.targets = ScrapingTargets()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.pdf = PDFConfig()
        self.security = SecurityConfig()
        
        # Carregar configurações do ambiente
        self._load_from_environment()
        
        # Criar diretórios necessários
        self._create_directories()
    
    def _load_from_environment(self):
        """Carrega configurações das variáveis de ambiente"""
        # Configurações do navegador
        self.browser.headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
        self.browser.timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))
        self.browser.rate_limit = float(os.getenv("RATE_LIMIT", "1.0"))
        
        # Configurações da API
        self.api.base_url = os.getenv("RADAR_API_URL", "http://localhost:8080")
        self.api.timeout = int(os.getenv("API_TIMEOUT", "30"))
        
        # URLs dos sites (devem ser configuradas para cada universidade)
        self.targets.university_portal = os.getenv("UNIVERSITY_PORTAL_URL", self.targets.university_portal)
        self.targets.course_catalog = os.getenv("COURSE_CATALOG_URL", self.targets.course_catalog)
        self.targets.schedule_system = os.getenv("SCHEDULE_SYSTEM_URL", self.targets.schedule_system)
        
        # Configurações de logging
        self.logging.level = os.getenv("LOG_LEVEL", "INFO")
        
        # Configurações de segurança
        self.security.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
        
        # Credenciais (se necessário)
        if os.getenv("PORTAL_USERNAME") and os.getenv("PORTAL_PASSWORD"):
            self.targets.login_required = True
            self.portal_credentials = {
                "username": os.getenv("PORTAL_USERNAME"),
                "password": os.getenv("PORTAL_PASSWORD")
            }
    
    def _create_directories(self):
        """Cria diretórios necessários se não existirem"""
        directories = [
            self.logging.log_dir,
            self.pdf.temp_dir,
            Path("screenshots"),
            Path("downloads")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_scraper_config(self, scraper_type: str) -> Dict[str, Any]:
        """
        Retorna configuração específica para um tipo de scraper.
        
        Args:
            scraper_type: Tipo do scraper (courses, schedules, etc.)
            
        Returns:
            Configuração específica
        """
        base_config = {
            "browser": self.browser,
            "rate_limit": self.browser.rate_limit,
            "timeout": self.browser.timeout,
            "user_agent": self.browser.user_agent
        }
        
        # Configurações específicas por tipo
        if scraper_type == "courses":
            base_config.update({
                "target_url": self.targets.course_catalog,
                "selectors": self.targets.course_selectors
            })
        elif scraper_type == "schedules":
            base_config.update({
                "target_url": self.targets.schedule_system,
                "selectors": self.targets.schedule_selectors
            })
        elif scraper_type == "syllabi":
            base_config.update({
                "target_url": self.targets.syllabus_repository,
                "pdf_config": self.pdf
            })
        
        return base_config
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o ambiente atual.
        
        Returns:
            Informações do ambiente
        """
        return {
            "python_version": os.sys.version,
            "working_directory": os.getcwd(),
            "environment_variables": {
                key: value for key, value in os.environ.items() 
                if key.startswith(("RADAR_", "BROWSER_", "LOG_"))
            },
            "config_summary": {
                "browser_headless": self.browser.headless,
                "api_url": self.api.base_url,
                "log_level": self.logging.level,
                "rate_limit": self.browser.rate_limit
            }
        }


# Instância global de configuração
config = Config()