"""
Configuração centralizada de logging para o projeto.

Fornece logger configurado com formatação consistente
e níveis apropriados para diferentes ambientes.
"""

import logging
import sys
from typing import Optional
from loguru import logger as loguru_logger


def configure_logging(level: str = "INFO", format_type: str = "detailed") -> None:
    """
    Configura o sistema de logging global.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Tipo de formatação (simple, detailed, json)
    """
    # Remove handlers padrão do loguru
    loguru_logger.remove()
    
    # Formato detalhado para desenvolvimento
    if format_type == "detailed":
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    # Formato simples para produção
    elif format_type == "simple":
        format_str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}"
    # Formato JSON para sistemas de monitoramento
    elif format_type == "json":
        format_str = (
            '{"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", "module": "{name}", '
            '"function": "{function}", "line": {line}, "message": "{message}"}'
        )
    else:
        format_str = "{time} | {level} | {name} | {message}"
    
    # Adicionar handler para stdout
    loguru_logger.add(
        sys.stdout,
        format=format_str,
        level=level,
        colorize=True if format_type != "json" else False,
        backtrace=True,
        diagnose=True
    )
    
    # Handler para arquivo de log (opcional)
    loguru_logger.add(
        "logs/radar_webscrapping.log",
        format=format_str,
        level=level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )


def get_logger(name: Optional[str] = None) -> loguru_logger:
    """
    Obtém logger configurado para um módulo.
    
    Args:
        name: Nome do módulo/classe
        
    Returns:
        Logger configurado
    """
    if name:
        return loguru_logger.bind(name=name)
    return loguru_logger


class StructuredLogger:
    """
    Logger estruturado para contextos específicos.
    
    Facilita logging com campos estruturados para melhor
    observabilidade e debugging.
    """
    
    def __init__(self, context: str, **extra_fields):
        self.context = context
        self.extra_fields = extra_fields
        self.logger = loguru_logger.bind(context=context, **extra_fields)
    
    def info(self, message: str, **fields):
        """Log de informação com campos estruturados."""
        self.logger.bind(**fields).info(message)
    
    def warning(self, message: str, **fields):
        """Log de warning com campos estruturados."""
        self.logger.bind(**fields).warning(message)
    
    def error(self, message: str, **fields):
        """Log de erro com campos estruturados."""
        self.logger.bind(**fields).error(message)
    
    def debug(self, message: str, **fields):
        """Log de debug com campos estruturados."""
        self.logger.bind(**fields).debug(message)
    
    def critical(self, message: str, **fields):
        """Log crítico com campos estruturados."""
        self.logger.bind(**fields).critical(message)


def create_scraping_logger(scraper_name: str, job_id: Optional[str] = None) -> StructuredLogger:
    """
    Cria logger específico para scraping.
    
    Args:
        scraper_name: Nome do scraper
        job_id: ID do job de scraping
        
    Returns:
        Logger estruturado para scraping
    """
    extra_fields = {"scraper": scraper_name}
    if job_id:
        extra_fields["job_id"] = job_id
    
    return StructuredLogger("scraping", **extra_fields)


def create_use_case_logger(use_case_name: str, session_id: Optional[str] = None) -> StructuredLogger:
    """
    Cria logger específico para casos de uso.
    
    Args:
        use_case_name: Nome do caso de uso
        session_id: ID da sessão
        
    Returns:
        Logger estruturado para casos de uso
    """
    extra_fields = {"use_case": use_case_name}
    if session_id:
        extra_fields["session_id"] = session_id
    
    return StructuredLogger("use_case", **extra_fields)


# Configurar logging por padrão
configure_logging()