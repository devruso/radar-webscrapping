"""
Interface para repositório de cursos.

Define o contrato para persistência e recuperação de cursos,
seguindo o padrão Repository para abstrair detalhes de armazenamento.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ...domain.entities import Curso
from ...domain.value_objects import CodigoCurso


class ICursoRepository(ABC):
    """
    Interface para repositório de cursos.
    
    Define operações de persistência para a entidade Curso,
    abstraindo detalhes de implementação de armazenamento.
    """
    
    @abstractmethod
    async def salvar(self, curso: Curso) -> None:
        """
        Salva um curso no repositório.
        
        Args:
            curso: Curso a ser salvo
        """
        pass
    
    @abstractmethod
    async def obter_por_id(self, id: UUID) -> Optional[Curso]:
        """
        Obtém curso por ID.
        
        Args:
            id: ID único do curso
            
        Returns:
            Curso encontrado ou None
        """
        pass
    
    @abstractmethod
    async def obter_por_codigo(self, codigo: CodigoCurso) -> Optional[Curso]:
        """
        Obtém curso por código.
        
        Args:
            codigo: Código do curso no SIGAA
            
        Returns:
            Curso encontrado ou None
        """
        pass
    
    @abstractmethod
    async def listar_todos(self) -> List[Curso]:
        """
        Lista todos os cursos.
        
        Returns:
            Lista de todos os cursos
        """
        pass
    
    @abstractmethod
    async def listar_por_unidade(self, unidade: str) -> List[Curso]:
        """
        Lista cursos por unidade de vinculação.
        
        Args:
            unidade: Nome da unidade
            
        Returns:
            Lista de cursos da unidade
        """
        pass
    
    @abstractmethod
    async def existe(self, codigo: CodigoCurso) -> bool:
        """
        Verifica se curso existe.
        
        Args:
            codigo: Código do curso
            
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def excluir(self, id: UUID) -> bool:
        """
        Exclui curso por ID.
        
        Args:
            id: ID do curso
            
        Returns:
            True se excluído, False se não encontrado
        """
        pass
    
    @abstractmethod
    async def contar_total(self) -> int:
        """
        Conta total de cursos.
        
        Returns:
            Número total de cursos
        """
        pass