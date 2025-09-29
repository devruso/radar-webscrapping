"""
Módulo de casos de uso da aplicação.

Contém a lógica de negócio específica da aplicação,
orquestrando operações entre domínio e infraestrutura.
"""

from .ScrapearCursosUseCase import ScrapearCursosUseCase
from .ScrapearComponentesUseCase import ScrapearComponentesUseCase
from .ScrapearEstruturasCurricularesUseCase import ScrapearEstruturasCurricularesUseCase
from .OrquestrarScrapingCompletoUseCase import (
    OrquestrarScrapingCompletoUseCase,
    TipoScrapingCompleto
)

__all__ = [
    'ScrapearCursosUseCase',
    'ScrapearComponentesUseCase', 
    'ScrapearEstruturasCurricularesUseCase',
    'OrquestrarScrapingCompletoUseCase',
    'TipoScrapingCompleto'
]