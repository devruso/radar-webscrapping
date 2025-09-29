"""
Interface para cliente da API do radar-webapi.

Define contrato para comunicação com o backend principal do sistema.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

from ...domain.entities import Curso, ComponenteCurricular, EstruturaCurricular


class StatusSincronizacao(Enum):
    """Status da sincronização com o backend."""
    SUCESSO = "sucesso"
    ERRO = "erro"
    PARCIAL = "parcial"


class ResultadoSincronizacao:
    """Resultado de uma operação de sincronização."""
    
    def __init__(self, 
                 status: StatusSincronizacao,
                 itens_processados: int,
                 itens_com_erro: int = 0,
                 detalhes: Optional[str] = None):
        self.status = status
        self.itens_processados = itens_processados
        self.itens_com_erro = itens_com_erro
        self.detalhes = detalhes
    
    @property
    def sucesso_total(self) -> bool:
        """Indica se a sincronização foi 100% bem-sucedida."""
        return self.status == StatusSincronizacao.SUCESSO and self.itens_com_erro == 0


class IRadarApiClient(ABC):
    """
    Interface para cliente da API do radar-webapi.
    
    Define operações de comunicação com o backend principal,
    abstraindo detalhes de implementação HTTP.
    """
    
    @abstractmethod
    async def verificar_saude(self) -> bool:
        """
        Verifica se a API está funcionando.
        
        Returns:
            True se API está saudável, False caso contrário
        """
        pass
    
    @abstractmethod
    async def enviar_cursos(self, cursos: List[Curso]) -> ResultadoSincronizacao:
        """
        Envia lista de cursos para o backend.
        
        Args:
            cursos: Lista de cursos a serem enviados
            
        Returns:
            Resultado da sincronização
        """
        pass
    
    @abstractmethod
    async def enviar_componentes(self, 
                                componentes: List[ComponenteCurricular]) -> ResultadoSincronizacao:
        """
        Envia lista de componentes curriculares para o backend.
        
        Args:
            componentes: Lista de componentes a serem enviados
            
        Returns:
            Resultado da sincronização
        """
        pass
    
    @abstractmethod
    async def enviar_estruturas(self, 
                               estruturas: List[EstruturaCurricular]) -> ResultadoSincronizacao:
        """
        Envia lista de estruturas curriculares para o backend.
        
        Args:
            estruturas: Lista de estruturas a serem enviadas
            
        Returns:
            Resultado da sincronização
        """
        pass
    
    @abstractmethod
    async def sincronizar_tudo(self,
                              cursos: List[Curso],
                              componentes: List[ComponenteCurricular], 
                              estruturas: List[EstruturaCurricular]) -> Dict[str, ResultadoSincronizacao]:
        """
        Sincroniza todos os dados de uma vez.
        
        Args:
            cursos: Lista de cursos
            componentes: Lista de componentes
            estruturas: Lista de estruturas
            
        Returns:
            Dicionário com resultados por tipo de dados
        """
        pass
    
    @abstractmethod
    async def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do backend.
        
        Returns:
            Dicionário com estatísticas da aplicação
        """
        pass
    
    @abstractmethod
    async def curso_existe(self, codigo_curso: str) -> bool:
        """
        Verifica se curso existe no backend.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def componente_existe(self, codigo_componente: str) -> bool:
        """
        Verifica se componente existe no backend.
        
        Args:
            codigo_componente: Código do componente
            
        Returns:
            True se existe, False caso contrário
        """
        pass