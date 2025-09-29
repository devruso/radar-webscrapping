"""
Interface para serviços de scraping.

Define contratos para os diferentes tipos de scrapers,
abstraindo detalhes de implementação técnica.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

from ...domain.entities import Curso, ComponenteCurricular, EstruturaCurricular


class TipoScraping(Enum):
    """Tipos de scraping disponíveis."""
    CURSOS = "cursos"
    COMPONENTES = "componentes"
    ESTRUTURAS_CURRICULARES = "estruturas_curriculares"


class IScrapingService(ABC):
    """
    Interface base para serviços de scraping.
    
    Define operações comuns para todos os tipos de scrapers.
    """
    
    @abstractmethod
    async def scrape(self, configuracao: Dict[str, Any]) -> List[Any]:
        """
        Executa o processo de scraping.
        
        Args:
            configuracao: Parâmetros de configuração específicos
            
        Returns:
            Lista de dados coletados
        """
        pass
    
    @abstractmethod
    async def validar_configuracao(self, configuracao: Dict[str, Any]) -> bool:
        """
        Valida se a configuração está correta.
        
        Args:
            configuracao: Configuração a ser validada
            
        Returns:
            True se válida, False caso contrário
        """
        pass
    
    @abstractmethod
    def obter_tipo_scraping(self) -> TipoScraping:
        """
        Obtém o tipo de scraping deste serviço.
        
        Returns:
            Tipo de scraping
        """
        pass


class ICursoScrapingService(IScrapingService):
    """
    Interface para scraping de cursos.
    
    Especializa o scraping para coleta de dados de cursos.
    """
    
    @abstractmethod
    async def scrape_cursos(self, 
                           filtro_unidade: Optional[str] = None,
                           filtro_modalidade: Optional[str] = None) -> List[Curso]:
        """
        Executa scraping específico de cursos.
        
        Args:
            filtro_unidade: Filtrar por unidade específica
            filtro_modalidade: Filtrar por modalidade específica
            
        Returns:
            Lista de cursos coletados
        """
        pass
    
    @abstractmethod
    async def obter_detalhes_curso(self, codigo_curso: str) -> Optional[Curso]:
        """
        Obtém detalhes específicos de um curso.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Dados detalhados do curso ou None
        """
        pass


class IComponenteScrapingService(IScrapingService):
    """
    Interface para scraping de componentes curriculares.
    """
    
    @abstractmethod
    async def scrape_componentes(self,
                                filtro_nome: Optional[str] = None,
                                filtro_departamento: Optional[str] = None,
                                filtro_tipo: Optional[str] = None) -> List[ComponenteCurricular]:
        """
        Executa scraping de componentes curriculares.
        
        Args:
            filtro_nome: Filtrar por nome da disciplina
            filtro_departamento: Filtrar por departamento
            filtro_tipo: Filtrar por tipo de componente
            
        Returns:
            Lista de componentes coletados
        """
        pass
    
    @abstractmethod
    async def obter_programa_componente(self, codigo_componente: str) -> Optional[str]:
        """
        Obtém programa/ementa de um componente específico.
        
        Args:
            codigo_componente: Código do componente
            
        Returns:
            Programa do componente ou None
        """
        pass


class IEstruturaCurricularScrapingService(IScrapingService):
    """
    Interface para scraping de estruturas curriculares.
    """
    
    @abstractmethod
    async def scrape_estruturas(self, 
                               codigo_curso: Optional[str] = None) -> List[EstruturaCurricular]:
        """
        Executa scraping de estruturas curriculares.
        
        Args:
            codigo_curso: Filtrar por curso específico
            
        Returns:
            Lista de estruturas curriculares coletadas
        """
        pass
    
    @abstractmethod
    async def obter_relatorio_estrutura(self, codigo_estrutura: str) -> Optional[EstruturaCurricular]:
        """
        Obtém relatório detalhado de uma estrutura curricular.
        
        Args:
            codigo_estrutura: Código da estrutura
            
        Returns:
            Estrutura curricular detalhada ou None
        """
        pass


class IScrapingFactory(ABC):
    """
    Interface para factory de scrapers.
    
    Responsável por criar instâncias dos serviços de scraping apropriados.
    """
    
    @abstractmethod
    def criar_curso_scraper(self) -> ICursoScrapingService:
        """
        Cria instância do scraper de cursos.
        
        Returns:
            Serviço de scraping de cursos
        """
        pass
    
    @abstractmethod
    def criar_componente_scraper(self) -> IComponenteScrapingService:
        """
        Cria instância do scraper de componentes.
        
        Returns:
            Serviço de scraping de componentes
        """
        pass
    
    @abstractmethod
    def criar_estrutura_scraper(self) -> IEstruturaCurricularScrapingService:
        """
        Cria instância do scraper de estruturas.
        
        Returns:
            Serviço de scraping de estruturas curriculares
        """
        pass