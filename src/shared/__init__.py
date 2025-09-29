"""
Módulo compartilhado com utilitários e configurações.

Contém funcionalidades compartilhadas entre diferentes
camadas da aplicação.
"""

from .logging import get_logger, configure_logging, StructuredLogger

__all__ = [
    'get_logger',
    'configure_logging', 
    'StructuredLogger'
]