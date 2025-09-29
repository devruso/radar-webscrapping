"""
Exceções do domínio Radar.

Exporta todas as exceções customizadas do sistema.
"""

from .RadarExceptions import (
    RadarException,
    DomainException,
    ApplicationException,
    InfrastructureException,
    CursoInvalidoException,
    ComponenteCurricularInvalidoException,
    EstruturaCurricularInvalidaException,
    PreRequisitoInvalidoException,
    ScrapingException,
    ValidationException,
    SincronizacaoException,
    NetworkException,
    BrowserException,
    ConfigurationException
)

__all__ = [
    "RadarException",
    "DomainException", 
    "ApplicationException",
    "InfrastructureException",
    "CursoInvalidoException",
    "ComponenteCurricularInvalidoException",
    "EstruturaCurricularInvalidaException", 
    "PreRequisitoInvalidoException",
    "ScrapingException",
    "ValidationException",
    "SincronizacaoException",
    "NetworkException",
    "BrowserException",
    "ConfigurationException"
]