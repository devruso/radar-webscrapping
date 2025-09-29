"""
Entidades do domínio Radar.

Exporta todas as entidades principais do sistema.
"""

from .Curso import Curso
from .ComponenteCurricular import ComponenteCurricular
from .EstruturaCurricular import EstruturaCurricular, ComponenteEstrutura

__all__ = [
    "Curso",
    "ComponenteCurricular", 
    "EstruturaCurricular",
    "ComponenteEstrutura"
]