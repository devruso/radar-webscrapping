"""
Exceções customizadas do domínio Radar.

Este módulo define a hierarquia de exceções específicas do domínio,
seguindo o princípio de que exceções são parte da linguagem ubíqua.
"""

from typing import Optional


class RadarException(Exception):
    """Exceção base para todos os erros do sistema Radar."""
    
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class DomainException(RadarException):
    """Exceções relacionadas às regras de negócio do domínio."""
    pass


class ApplicationException(RadarException):
    """Exceções relacionadas aos casos de uso da aplicação."""
    pass


class InfrastructureException(RadarException):
    """Exceções relacionadas à infraestrutura técnica."""
    pass


# Exceções específicas do domínio
class CursoInvalidoException(DomainException):
    """Lançada quando dados de curso não atendem às regras de negócio."""
    
    def __init__(self, codigo_curso: str, motivo: str) -> None:
        message = f"Curso inválido [{codigo_curso}]: {motivo}"
        super().__init__(message)
        self.codigo_curso = codigo_curso


class ComponenteCurricularInvalidoException(DomainException):
    """Lançada quando componente curricular possui dados inválidos."""
    
    def __init__(self, codigo_componente: str, motivo: str) -> None:
        message = f"Componente curricular inválido [{codigo_componente}]: {motivo}"
        super().__init__(message)
        self.codigo_componente = codigo_componente


class EstruturaCurricularInvalidaException(DomainException):
    """Lançada quando estrutura curricular não atende às regras."""
    
    def __init__(self, codigo_estrutura: str, motivo: str) -> None:
        message = f"Estrutura curricular inválida [{codigo_estrutura}]: {motivo}"
        super().__init__(message)
        self.codigo_estrutura = codigo_estrutura


class PreRequisitoInvalidoException(DomainException):
    """Lançada quando pré-requisito não pode ser processado."""
    
    def __init__(self, expressao: str, motivo: str) -> None:
        message = f"Pré-requisito inválido [{expressao}]: {motivo}"
        super().__init__(message)
        self.expressao = expressao


# Exceções da camada de aplicação
class ScrapingException(ApplicationException):
    """Lançada quando processo de scraping falha."""
    
    def __init__(self, url: str, motivo: str) -> None:
        message = f"Falha no scraping de [{url}]: {motivo}"
        super().__init__(message)
        self.url = url


class ValidationException(ApplicationException):
    """Lançada quando validação de dados falha."""
    
    def __init__(self, campo: str, valor: str, motivo: str) -> None:
        message = f"Validação falhou para [{campo}={valor}]: {motivo}"
        super().__init__(message)
        self.campo = campo
        self.valor = valor


class SincronizacaoException(ApplicationException):
    """Lançada quando sincronização com radar-webapi falha."""
    
    def __init__(self, endpoint: str, motivo: str) -> None:
        message = f"Falha na sincronização com [{endpoint}]: {motivo}"
        super().__init__(message)
        self.endpoint = endpoint


# Exceções da camada de infraestrutura
class NetworkException(InfrastructureException):
    """Lançada quando operações de rede falham."""
    
    def __init__(self, url: str, status_code: Optional[int] = None) -> None:
        message = f"Erro de rede ao acessar [{url}]"
        if status_code:
            message += f" - Status: {status_code}"
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class BrowserException(InfrastructureException):
    """Lançada quando operações do browser falham."""
    
    def __init__(self, operacao: str, motivo: str) -> None:
        message = f"Erro no browser durante [{operacao}]: {motivo}"
        super().__init__(message)
        self.operacao = operacao


class ConfigurationException(InfrastructureException):
    """Lançada quando configuração está inválida."""
    
    def __init__(self, parametro: str, motivo: str) -> None:
        message = f"Configuração inválida [{parametro}]: {motivo}"
        super().__init__(message)
        self.parametro = parametro