"""
Camada de domínio do sistema Radar.

Esta camada contém as regras de negócio mais importantes do sistema,
incluindo entidades, value objects e serviços de domínio.

A camada de domínio é o coração da aplicação e deve ser independente
de frameworks, bibliotecas externas ou detalhes de infraestrutura.
"""

from .entities import *
from .value_objects import *
from .exceptions import *

__version__ = "1.0.0"