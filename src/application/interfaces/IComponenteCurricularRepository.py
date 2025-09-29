"""
Interface para repositório de componentes curriculares.

Define o contrato para persistência e recuperação de componentes curriculares.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set
from uuid import UUID

from ...domain.entities import ComponenteCurricular
from ...domain.value_objects import CodigoComponente, TipoComponente


class IComponenteCurricularRepository(ABC):
    """
    Interface para repositório de componentes curriculares.
    
    Define operações de persistência para a entidade ComponenteCurricular.
    """
    
    @abstractmethod
    async def salvar(self, componente: ComponenteCurricular) -> None:
        """
        Salva um componente curricular.
        
        Args:
            componente: Componente a ser salvo
        """
        pass
    
    @abstractmethod
    async def obter_por_id(self, id: UUID) -> Optional[ComponenteCurricular]:
        """
        Obtém componente por ID.
        
        Args:
            id: ID único do componente
            
        Returns:
            Componente encontrado ou None
        """
        pass
    
    @abstractmethod
    async def obter_por_codigo(self, codigo: CodigoComponente) -> Optional[ComponenteCurricular]:
        """
        Obtém componente por código.
        
        Args:
            codigo: Código do componente
            
        Returns:
            Componente encontrado ou None
        """
        pass
    
    @abstractmethod
    async def listar_todos(self) -> List[ComponenteCurricular]:
        """
        Lista todos os componentes curriculares.
        
        Returns:
            Lista de todos os componentes
        """
        pass
    
    @abstractmethod
    async def listar_por_tipo(self, tipo: TipoComponente) -> List[ComponenteCurricular]:
        """
        Lista componentes por tipo.
        
        Args:
            tipo: Tipo do componente
            
        Returns:
            Lista de componentes do tipo especificado
        """
        pass
    
    @abstractmethod
    async def listar_por_departamento(self, departamento: str) -> List[ComponenteCurricular]:
        """
        Lista componentes por departamento.
        
        Args:
            departamento: Código do departamento (ex: MATA, MATC)
            
        Returns:
            Lista de componentes do departamento
        """
        pass
    
    @abstractmethod
    async def buscar_por_nome(self, termo_busca: str) -> List[ComponenteCurricular]:
        """
        Busca componentes por nome.
        
        Args:
            termo_busca: Termo a ser buscado no nome
            
        Returns:
            Lista de componentes que contêm o termo
        """
        pass
    
    @abstractmethod
    async def listar_prerequisitos(self, codigo: CodigoComponente) -> Set[str]:
        """
        Lista pré-requisitos de um componente.
        
        Args:
            codigo: Código do componente
            
        Returns:
            Set de códigos dos pré-requisitos
        """
        pass
    
    @abstractmethod
    async def listar_dependentes(self, codigo: CodigoComponente) -> List[ComponenteCurricular]:
        """
        Lista componentes que dependem do código informado.
        
        Args:
            codigo: Código do componente
            
        Returns:
            Lista de componentes que têm este como pré-requisito
        """
        pass
    
    @abstractmethod
    async def existe(self, codigo: CodigoComponente) -> bool:
        """
        Verifica se componente existe.
        
        Args:
            codigo: Código do componente
            
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def excluir(self, id: UUID) -> bool:
        """
        Exclui componente por ID.
        
        Args:
            id: ID do componente
            
        Returns:
            True se excluído, False se não encontrado
        """
        pass