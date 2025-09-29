"""
Entidade EstruturaCurricular do domínio Radar.

Representa uma estrutura curricular de um curso, contendo
informações sobre matriz curricular, prazos e componentes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..value_objects.ValueObjects import (
    CodigoCurso, AnoPeriodo, SituacaoEstrutura, PrazoConclusao, 
    CargaHoraria, NaturezaComponente
)
from ..exceptions.RadarExceptions import EstruturaCurricularInvalidaException


@dataclass
class ComponenteEstrutura:
    """
    Representa um componente dentro de uma estrutura curricular.
    
    Contém informações específicas sobre como o componente
    se relaciona com a estrutura (período, natureza, etc.).
    """
    codigo_componente: str
    periodo_sugerido: int
    natureza: NaturezaComponente
    carga_horaria: CargaHoraria
    
    def __post_init__(self) -> None:
        if self.periodo_sugerido < 0 or self.periodo_sugerido > 20:
            raise EstruturaCurricularInvalidaException(
                "N/A",
                f"Período sugerido inválido: {self.periodo_sugerido}"
            )


@dataclass
class EstruturaCurricular:
    """
    Entidade que representa uma estrutura curricular de um curso.
    
    Agrega informações sobre matriz curricular, prazos de conclusão
    e componentes organizados por período.
    """
    
    # Identificador único
    id: UUID = field(default_factory=uuid4)
    
    # Dados obrigatórios
    codigo: str = field()  # Ex: G20251X
    codigo_curso: CodigoCurso = field()
    matriz_curricular: str = field()
    ano_periodo_vigencia: AnoPeriodo = field()
    situacao: SituacaoEstrutura = field()
    
    # Informações do curso
    unidade_vinculacao: str = field()
    municipio_funcionamento: str = field()
    
    # Prazos e cargas horárias
    prazos_conclusao: PrazoConclusao = field()
    carga_horaria_obrigatoria: int = field()
    carga_horaria_optativa: int = field()
    carga_horaria_complementar: int = field()
    carga_horaria_optativa_livre: int = 0
    
    # Componentes por período
    componentes_por_periodo: Dict[int, List[ComponenteEstrutura]] = field(default_factory=dict)
    
    # Metadados
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    url_origem: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validações pós-inicialização."""
        self._validar_dados_obrigatorios()
        self._validar_regras_negocio()
    
    def _validar_dados_obrigatorios(self) -> None:
        """Valida se todos os dados obrigatórios estão presentes."""
        if not self.codigo.strip():
            raise EstruturaCurricularInvalidaException(
                "N/A",
                "Código da estrutura é obrigatório"
            )
        
        if not self.matriz_curricular.strip():
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                "Matriz curricular é obrigatória"
            )
        
        if not self.unidade_vinculacao.strip():
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                "Unidade de vinculação é obrigatória"
            )
    
    def _validar_regras_negocio(self) -> None:
        """Valida regras específicas de negócio."""
        # Validar cargas horárias
        if any(carga < 0 for carga in [
            self.carga_horaria_obrigatoria,
            self.carga_horaria_optativa, 
            self.carga_horaria_complementar,
            self.carga_horaria_optativa_livre
        ]):
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                "Cargas horárias não podem ser negativas"
            )
        
        # Validar total de carga horária
        total_calculado = (self.carga_horaria_obrigatoria + 
                          self.carga_horaria_optativa + 
                          self.carga_horaria_complementar)
        
        if total_calculado == 0:
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                "Carga horária total deve ser maior que zero"
            )
    
    def adicionar_componente(self, 
                           periodo: int,
                           codigo_componente: str,
                           natureza: NaturezaComponente,
                           carga_horaria: CargaHoraria) -> None:
        """
        Adiciona um componente à estrutura curricular.
        
        Args:
            periodo: Período sugerido do componente (0 = optativa)
            codigo_componente: Código do componente
            natureza: Natureza do componente (obrigatório, optativo, etc.)
            carga_horaria: Carga horária do componente
        """
        if periodo < 0:
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                f"Período inválido: {periodo}"
            )
        
        componente = ComponenteEstrutura(
            codigo_componente=codigo_componente,
            periodo_sugerido=periodo,
            natureza=natureza,
            carga_horaria=carga_horaria
        )
        
        if periodo not in self.componentes_por_periodo:
            self.componentes_por_periodo[periodo] = []
        
        # Verificar se componente já existe no período
        codigos_existentes = [c.codigo_componente for c in self.componentes_por_periodo[periodo]]
        if codigo_componente in codigos_existentes:
            raise EstruturaCurricularInvalidaException(
                self.codigo,
                f"Componente {codigo_componente} já existe no período {periodo}"
            )
        
        self.componentes_por_periodo[periodo].append(componente)
        self.atualizado_em = datetime.now()
    
    def remover_componente(self, periodo: int, codigo_componente: str) -> None:
        """
        Remove um componente da estrutura curricular.
        
        Args:
            periodo: Período do componente
            codigo_componente: Código do componente a ser removido
        """
        if periodo not in self.components_por_periodo:
            return
        
        self.componentes_por_periodo[periodo] = [
            c for c in self.componentes_por_periodo[periodo]
            if c.codigo_componente != codigo_componente
        ]
        
        # Remove período se ficou vazio
        if not self.componentes_por_periodo[periodo]:
            del self.componentes_por_periodo[periodo]
        
        self.atualizado_em = datetime.now()
    
    def obter_componentes_periodo(self, periodo: int) -> List[ComponenteEstrutura]:
        """
        Obtém componentes de um período específico.
        
        Args:
            periodo: Período desejado
            
        Returns:
            Lista de componentes do período
        """
        return self.componentes_por_periodo.get(periodo, [])
    
    def obter_componentes_obrigatorios(self) -> List[ComponenteEstrutura]:
        """Obtém todos os componentes obrigatórios."""
        componentes = []
        for periodo_componentes in self.componentes_por_periodo.values():
            componentes.extend([
                c for c in periodo_componentes 
                if c.natureza == NaturezaComponente.OBRIGATORIO
            ])
        return componentes
    
    def obter_componentes_optativos(self) -> List[ComponenteEstrutura]:
        """Obtém todos os componentes optativos."""
        componentes = []
        for periodo_componentes in self.componentes_por_periodo.values():
            componentes.extend([
                c for c in periodo_componentes 
                if c.natureza == NaturezaComponente.OPTATIVO
            ])
        return componentes
    
    def calcular_carga_horaria_total(self) -> int:
        """Calcula carga horária total baseada nos componentes."""
        total = 0
        for periodo_componentes in self.componentes_por_periodo.values():
            total += sum(c.carga_horaria.total for c in periodo_componentes)
        return total
    
    def obter_quantidade_periodos(self) -> int:
        """Obtém a quantidade de períodos da estrutura."""
        if not self.componentes_por_periodo:
            return 0
        return max(p for p in self.componentes_por_periodo.keys() if p > 0)
    
    @property
    def carga_horaria_total(self) -> int:
        """Carga horária total definida."""
        return (self.carga_horaria_obrigatoria + 
                self.carga_horaria_optativa + 
                self.carga_horaria_complementar)
    
    @property
    def esta_ativa(self) -> bool:
        """Verifica se a estrutura está ativa."""
        return self.situacao == SituacaoEstrutura.ATIVA
    
    def ativar(self) -> None:
        """Ativa a estrutura curricular."""
        self.situacao = SituacaoEstrutura.ATIVA
        self.atualizado_em = datetime.now()
    
    def consolidar(self) -> None:
        """Consolida a estrutura curricular."""
        self.situacao = SituacaoEstrutura.CONSOLIDADA
        self.atualizado_em = datetime.now()
    
    def inativar(self) -> None:
        """Inativa a estrutura curricular."""
        self.situacao = SituacaoEstrutura.INATIVA
        self.atualizado_em = datetime.now()
    
    def __eq__(self, other) -> bool:
        """Estruturas são iguais se têm o mesmo código."""
        if not isinstance(other, EstruturaCurricular):
            return False
        return self.codigo == other.codigo
    
    def __hash__(self) -> int:
        """Hash baseado no código da estrutura."""
        return hash(self.codigo)
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.matriz_curricular} ({self.situacao.value})"
    
    def __repr__(self) -> str:
        return f"EstruturaCurricular(codigo='{self.codigo}', situacao={self.situacao})"