"""
Classe base para todos os scrapers do projeto Radar.

Este módulo define a arquitetura base que todos os scrapers devem seguir:
1. Interface padrão (ScraperInterface)
2. Classe base com funcionalidades comuns (BaseScraper)
3. Sistema de retry e tratamento de erros
4. Logging padronizado
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.scraped_data import BaseScrapedData, ScrapingJob, ScrapingStatus, ScrapingType


class ScraperInterface(ABC):
    """Interface que define o contrato para todos os scrapers"""
    
    @abstractmethod
    async def scrape(self, config: Dict[str, Any] = None) -> List[BaseScrapedData]:
        """
        Método principal de scraping.
        
        Args:
            config: Configurações específicas para este scraping
            
        Returns:
            Lista de dados coletados
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida se a configuração fornecida é válida para este scraper.
        
        Args:
            config: Configuração a ser validada
            
        Returns:
            True se válida, False caso contrário
        """
        pass
    
    @property
    @abstractmethod
    def scraper_name(self) -> str:
        """Nome único do scraper"""
        pass
    
    @property
    @abstractmethod
    def scraping_type(self) -> ScrapingType:
        """Tipo de scraping que este scraper realiza"""
        pass


class BaseScraper(ScraperInterface):
    """
    Classe base que implementa funcionalidades comuns a todos os scrapers.
    
    Fornece:
    - Sistema de retry automático
    - Logging padronizado
    - Controle de rate limiting
    - Tratamento de erros
    - Métricas básicas
    """
    
    def __init__(self, base_url: str = None, rate_limit: float = 1.0):
        """
        Inicializa o scraper base.
        
        Args:
            base_url: URL base para o scraping
            rate_limit: Intervalo mínimo entre requisições (segundos)
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session_stats = {
            'requests_made': 0,
            'errors_occurred': 0,
            'data_collected': 0,
            'session_start': datetime.now()
        }
        
        # Configurar logger específico para este scraper
        self.logger = logger.bind(scraper=self.scraper_name)
    
    async def scrape_with_job_tracking(self, job: ScrapingJob, config: Dict[str, Any] = None) -> List[BaseScrapedData]:
        """
        Executa o scraping com rastreamento de job.
        
        Args:
            job: Job de scraping para rastrear progresso
            config: Configurações específicas
            
        Returns:
            Lista de dados coletados
        """
        self.logger.info(f"Iniciando scraping job {job.job_id}")
        
        job.status = ScrapingStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Validar configuração
            if config and not self.validate_config(config):
                raise ValueError(f"Configuração inválida para {self.scraper_name}")
            
            # Executar scraping
            results = await self.scrape(config)
            
            # Atualizar job
            job.status = ScrapingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.results_count = len(results)
            job.progress = 100
            
            self.logger.info(f"Scraping job {job.job_id} completado com {len(results)} itens")
            return results
            
        except Exception as e:
            job.status = ScrapingStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = str(e)
            job.progress = 0
            
            self.logger.error(f"Scraping job {job.job_id} falhou: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def make_request(self, url: str, **kwargs) -> Any:
        """
        Faz uma requisição com retry automático e rate limiting.
        
        Args:
            url: URL para fazer a requisição
            **kwargs: Argumentos adicionais para a requisição
            
        Returns:
            Resposta da requisição
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        
        self.last_request_time = time.time()
        self.session_stats['requests_made'] += 1
        
        self.logger.debug(f"Fazendo requisição para: {url}")
        
        try:
            # Aqui seria implementada a lógica específica de requisição
            # (Playwright, requests, etc.)
            # Por enquanto, retornamos um placeholder
            return {"url": url, "status": "success"}
            
        except Exception as e:
            self.session_stats['errors_occurred'] += 1
            self.logger.error(f"Erro na requisição para {url}: {e}")
            raise
    
    def update_progress(self, job: ScrapingJob, current: int, total: int, message: str = ""):
        """
        Atualiza o progresso de um job.
        
        Args:
            job: Job a ser atualizado
            current: Número atual de itens processados
            total: Total de itens a processar
            message: Mensagem adicional de status
        """
        if total > 0:
            job.progress = min(100, int((current / total) * 100))
        
        self.logger.info(f"Progresso {job.job_id}: {current}/{total} ({job.progress}%) - {message}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da sessão atual.
        
        Returns:
            Dicionário com estatísticas
        """
        now = datetime.now()
        duration = (now - self.session_stats['session_start']).total_seconds()
        
        return {
            **self.session_stats,
            'session_duration_seconds': duration,
            'requests_per_minute': (self.session_stats['requests_made'] / duration) * 60 if duration > 0 else 0,
            'error_rate': (self.session_stats['errors_occurred'] / self.session_stats['requests_made']) 
                         if self.session_stats['requests_made'] > 0 else 0
        }
    
    def reset_session_stats(self):
        """Reseta as estatísticas da sessão"""
        self.session_stats = {
            'requests_made': 0,
            'errors_occurred': 0,
            'data_collected': 0,
            'session_start': datetime.now()
        }
    
    # Métodos abstratos que devem ser implementados pelas subclasses
    @abstractmethod
    async def scrape(self, config: Dict[str, Any] = None) -> List[BaseScrapedData]:
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        pass
    
    @property
    @abstractmethod
    def scraper_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def scraping_type(self) -> ScrapingType:
        pass


class ScraperRegistry:
    """
    Registry para gerenciar todos os scrapers disponíveis.
    
    Permite:
    - Registrar novos scrapers
    - Buscar scrapers por tipo
    - Listar todos os scrapers disponíveis
    """
    
    def __init__(self):
        self._scrapers: Dict[ScrapingType, Type[BaseScraper]] = {}
    
    def register(self, scraper_class: Type[BaseScraper]):
        """
        Registra um novo scraper.
        
        Args:
            scraper_class: Classe do scraper a ser registrada
        """
        # Criar instância temporária para acessar propriedades
        temp_instance = scraper_class()
        scraping_type = temp_instance.scraping_type
        
        if scraping_type in self._scrapers:
            logger.warning(f"Sobrescrevendo scraper existente para tipo {scraping_type}")
        
        self._scrapers[scraping_type] = scraper_class
        logger.info(f"Scraper {temp_instance.scraper_name} registrado para tipo {scraping_type}")
    
    def get_scraper(self, scraping_type: ScrapingType) -> Optional[Type[BaseScraper]]:
        """
        Obtém um scraper por tipo.
        
        Args:
            scraping_type: Tipo de scraping desejado
            
        Returns:
            Classe do scraper ou None se não encontrado
        """
        return self._scrapers.get(scraping_type)
    
    def list_available_scrapers(self) -> Dict[ScrapingType, str]:
        """
        Lista todos os scrapers disponíveis.
        
        Returns:
            Dicionário mapeando tipo para nome do scraper
        """
        result = {}
        for scraping_type, scraper_class in self._scrapers.items():
            temp_instance = scraper_class()
            result[scraping_type] = temp_instance.scraper_name
        return result
    
    def create_scraper(self, scraping_type: ScrapingType, **kwargs) -> Optional[BaseScraper]:
        """
        Cria uma instância de scraper.
        
        Args:
            scraping_type: Tipo de scraping desejado
            **kwargs: Argumentos para o construtor do scraper
            
        Returns:
            Instância do scraper ou None se não encontrado
        """
        scraper_class = self.get_scraper(scraping_type)
        if scraper_class:
            return scraper_class(**kwargs)
        return None


# Instância global do registry
scraper_registry = ScraperRegistry()