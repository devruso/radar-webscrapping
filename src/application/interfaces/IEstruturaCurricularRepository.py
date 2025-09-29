"""
Interface para repositório de estruturas curriculares.

Define o contrato para operações de persistência e consulta de estruturas
curriculares seguindo o padrão Repository.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain.entities import EstruturaCurricular
from ...domain.value_objects import CodigoCurso


class IEstruturaCurricularRepository(ABC):
    """
    Interface para repositório de estruturas curriculares.
    
    Define operações de persistência e consulta para estruturas curriculares,
    mantendo a separação entre domínio e infraestrutura.
    """
    
    @abstractmethod
    async def salvar(self, estrutura: EstruturaCurricular) -> None:
        """
        Salva uma estrutura curricular.
        
        Args:
            estrutura: Estrutura curricular a ser salva
            
        Raises:
            RepositoryException: Em caso de erro na persistência
        """
        pass
    
    @abstractmethod
    async def buscar_por_codigo_e_versao(self, 
                                        codigo_curso: str,
                                        versao: str) -> Optional[EstruturaCurricular]:
        """
        Busca uma estrutura curricular por código do curso e versão.
        
        Args:
            codigo_curso: Código do curso relacionado
            versao: Versão da estrutura curricular
            
        Returns:
            Estrutura curricular encontrada ou None
        """
        pass
    
    @abstractmethod
    async def buscar_ativa_por_curso(self, codigo_curso: str) -> Optional[EstruturaCurricular]:
        """
        Busca a estrutura curricular ativa de um curso.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Estrutura ativa ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def listar_por_curso(self, codigo_curso: str) -> List[EstruturaCurricular]:
        """
        Lista todas as estruturas curriculares de um curso.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Lista de estruturas do curso
        """
        pass
    
    @abstractmethod
    async def listar_todas(self) -> List[EstruturaCurricular]:
        """
        Lista todas as estruturas curriculares.
        
        Returns:
            Lista com todas as estruturas
        """
        pass
    
    @abstractmethod
    async def listar_por_periodo(self, ano: int, semestre: int) -> List[EstruturaCurricular]:
        """
        Lista estruturas curriculares por período.
        
        Args:
            ano: Ano da estrutura
            semestre: Semestre da estrutura
            
        Returns:
            Lista de estruturas do período
        """
        pass
    
    @abstractmethod
    async def atualizar(self, estrutura: EstruturaCurricular) -> None:
        """
        Atualiza uma estrutura curricular existente.
        
        Args:
            estrutura: Estrutura curricular a ser atualizada
            
        Raises:
            RepositoryException: Em caso de erro na atualização
            EntityNotFoundException: Se a estrutura não for encontrada
        """
        pass
    
    @abstractmethod
    async def remover(self, codigo_curso: str, versao: str) -> bool:
        """
        Remove uma estrutura curricular.
        
        Args:
            codigo_curso: Código do curso relacionado
            versao: Versão da estrutura
            
        Returns:
            True se removida com sucesso, False se não encontrada
            
        Raises:
            RepositoryException: Em caso de erro na remoção
        """
        pass
    
    @abstractmethod
    async def existe(self, codigo_curso: str, versao: str) -> bool:
        """
        Verifica se uma estrutura curricular existe.
        
        Args:
            codigo_curso: Código do curso relacionado
            versao: Versão da estrutura
            
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def contar_por_curso(self, codigo_curso: str) -> int:
        """
        Conta quantas estruturas um curso possui.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Número de estruturas do curso
        """
        pass
    
    @abstractmethod
    async def listar_versoes_por_curso(self, codigo_curso: str) -> List[str]:
        """
        Lista as versões de estruturas curriculares de um curso.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Lista com as versões ordenadas
        """
        pass
    
    @abstractmethod
    async def buscar_estruturas_com_componente(self, 
                                             codigo_componente: str) -> List[EstruturaCurricular]:
        """
        Busca estruturas que contêm um componente específico.
        
        Args:
            codigo_componente: Código do componente curricular
            
        Returns:
            Lista de estruturas que contêm o componente
        """
        pass