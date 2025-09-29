"""
Value Objects do domínio Radar.

Value Objects são objetos sem identidade que encapsulam valores
e suas regras de validação. São imutáveis e compareáveis por valor.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set
import re
from ..exceptions.RadarExceptions import DomainException


class SituacaoEstrutura(Enum):
    """Possíveis situações de uma estrutura curricular."""
    ATIVA = "ATIVA"
    CONSOLIDADA = "CONSOLIDADA"
    INATIVA = "INATIVA"
    EM_ELABORACAO = "EM_ELABORACAO"


class TipoComponente(Enum):
    """Tipos de componentes curriculares."""
    DISCIPLINA = "DISCIPLINA"
    ATIVIDADE = "ATIVIDADE"
    TRABALHO_CONCLUSAO = "TRABALHO_CONCLUSAO"
    ESTAGIO = "ESTAGIO"


class ModalidadeEducacao(Enum):
    """Modalidades de educação."""
    PRESENCIAL = "Presencial"
    A_DISTANCIA = "a Distância"
    HIBRIDA = "Híbrida"


class NaturezaComponente(Enum):
    """Natureza do componente curricular."""
    OBRIGATORIO = "OBRIGATORIO"
    OPTATIVO = "OPTATIVO"
    COMPLEMENTAR = "COMPLEMENTAR"


@dataclass(frozen=True)
class CodigoCurso:
    """
    Value Object para código de curso no SIGAA.
    
    Formato esperado: Letras + números (ex: G20251X)
    """
    valor: str
    
    def __post_init__(self) -> None:
        if not self.valor:
            raise DomainException("Código do curso não pode ser vazio")
        
        if not re.match(r'^[A-Z]\d{5}[A-Z]?$', self.valor):
            raise DomainException(
                f"Código do curso inválido: {self.valor}. "
                "Formato esperado: Letra + 5 dígitos + Letra opcional"
            )
    
    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class CodigoComponente:
    """
    Value Object para código de componente curricular.
    
    Formato esperado: 4-6 letras + 2-3 dígitos (ex: MATA02, MATC73)
    """
    valor: str
    
    def __post_init__(self) -> None:
        if not self.valor:
            raise DomainException("Código do componente não pode ser vazio")
        
        if not re.match(r'^[A-Z]{4,6}\d{2,3}$', self.valor):
            raise DomainException(
                f"Código do componente inválido: {self.valor}. "
                "Formato esperado: 4-6 letras + 2-3 dígitos"
            )
    
    def __str__(self) -> str:
        return self.valor
    
    @property 
    def departamento(self) -> str:
        """Extrai o departamento do código (primeiras 4 letras)."""
        return self.valor[:4]


@dataclass(frozen=True)
class CargaHoraria:
    """
    Value Object para carga horária de componentes.
    
    Representa as diferentes cargas horárias possíveis.
    """
    aula_teorica_presencial: int = 0
    aula_pratica_presencial: int = 0
    aula_extensionista_presencial: int = 0
    aula_teorica_distancia: int = 0
    aula_pratica_distancia: int = 0
    aula_extensionista_distancia: int = 0
    
    def __post_init__(self) -> None:
        cargas = [
            self.aula_teorica_presencial,
            self.aula_pratica_presencial, 
            self.aula_extensionista_presencial,
            self.aula_teorica_distancia,
            self.aula_pratica_distancia,
            self.aula_extensionista_distancia
        ]
        
        if any(carga < 0 for carga in cargas):
            raise DomainException("Carga horária não pode ser negativa")
        
        if all(carga == 0 for carga in cargas):
            raise DomainException("Pelo menos uma carga horária deve ser maior que zero")
    
    @property
    def total_presencial(self) -> int:
        """Total de horas presenciais."""
        return (self.aula_teorica_presencial + 
                self.aula_pratica_presencial + 
                self.aula_extensionista_presencial)
    
    @property
    def total_distancia(self) -> int:
        """Total de horas a distância."""
        return (self.aula_teorica_distancia + 
                self.aula_pratica_distancia + 
                self.aula_extensionista_distancia)
    
    @property
    def total(self) -> int:
        """Carga horária total."""
        return self.total_presencial + self.total_distancia
    
    def __str__(self) -> str:
        return f"{self.total}h"


@dataclass(frozen=True)
class AnoPeriodo:
    """
    Value Object para ano-período letivo.
    
    Formato: YYYY.P onde P é 1 ou 2
    """
    ano: int
    periodo: int
    
    def __post_init__(self) -> None:
        if self.ano < 2000 or self.ano > 2100:
            raise DomainException(f"Ano inválido: {self.ano}")
        
        if self.periodo not in [1, 2]:
            raise DomainException(f"Período inválido: {self.periodo}. Deve ser 1 ou 2")
    
    def __str__(self) -> str:
        return f"{self.ano}.{self.periodo}"
    
    @classmethod
    def from_string(cls, valor: str) -> 'AnoPeriodo':
        """Cria AnoPeriodo a partir de string no formato YYYY.P"""
        try:
            ano_str, periodo_str = valor.split('.')
            return cls(int(ano_str), int(periodo_str))
        except (ValueError, AttributeError):
            raise DomainException(f"Formato de ano-período inválido: {valor}")


@dataclass(frozen=True)
class ExpressaoPreRequisito:
    """
    Value Object para expressão de pré-requisitos.
    
    Encapsula a lógica de parsing e validação de pré-requisitos.
    """
    expressao: str
    
    def __post_init__(self) -> None:
        if not self.expressao or self.expressao.strip() == "-":
            # Permite expressão vazia (sem pré-requisitos)
            object.__setattr__(self, 'expressao', "")
            return
        
        # Validar formato básico da expressão
        expressao_limpa = self.expressao.strip()
        if not self._validar_formato(expressao_limpa):
            raise DomainException(f"Formato de pré-requisito inválido: {self.expressao}")
        
        object.__setattr__(self, 'expressao', expressao_limpa)
    
    def _validar_formato(self, expressao: str) -> bool:
        """Valida se a expressão tem formato válido."""
        # Permitir parênteses, códigos de disciplinas, E, OU
        pattern = r'^[\(\)\sA-Z0-9EOU]+$'
        return re.match(pattern, expressao) is not None
    
    def obter_codigos_componentes(self) -> Set[str]:
        """Extrai códigos de componentes da expressão."""
        if not self.expressao:
            return set()
        
        # Encontrar todos os códigos no formato MATA02, MATC73, etc.
        codigos = re.findall(r'[A-Z]{4,6}\d{2,3}', self.expressao)
        return set(codigos)
    
    @property
    def tem_prerequisitos(self) -> bool:
        """Verifica se tem pré-requisitos definidos."""
        return bool(self.expressao)
    
    def __str__(self) -> str:
        return self.expressao if self.expressao else "Sem pré-requisitos"


@dataclass(frozen=True)
class NomeCurso:
    """
    Value Object para nome do curso.
    
    Encapsula regras de formatação e validação do nome.
    """
    valor: str
    
    def __post_init__(self) -> None:
        if not self.valor or not self.valor.strip():
            raise DomainException("Nome do curso não pode ser vazio")
        
        nome_limpo = self.valor.strip()
        if len(nome_limpo) < 3:
            raise DomainException("Nome do curso deve ter pelo menos 3 caracteres")
        
        if len(nome_limpo) > 200:
            raise DomainException("Nome do curso não pode exceder 200 caracteres")
        
        object.__setattr__(self, 'valor', nome_limpo)
    
    def __str__(self) -> str:
        return self.valor
    
    @property
    def abreviado(self) -> str:
        """Retorna versão abreviada do nome (primeiras palavras)."""
        palavras = self.valor.split()
        if len(palavras) <= 3:
            return self.valor
        return " ".join(palavras[:3]) + "..."


@dataclass(frozen=True)
class PrazoConclusao:
    """
    Value Object para prazos de conclusão de curso.
    
    Representa os prazos mínimo, médio e máximo em semestres.
    """
    minimo: int
    medio: int
    maximo: int
    
    def __post_init__(self) -> None:
        if any(prazo <= 0 for prazo in [self.minimo, self.medio, self.maximo]):
            raise DomainException("Prazos devem ser maiores que zero")
        
        if not self.minimo <= self.medio <= self.maximo:
            raise DomainException(
                "Prazos devem estar em ordem: mínimo ≤ médio ≤ máximo"
            )
    
    def __str__(self) -> str:
        return f"Min: {self.minimo}, Médio: {self.medio}, Máx: {self.maximo} semestres"