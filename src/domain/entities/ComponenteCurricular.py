"""
Entidade ComponenteCurricular do domínio Radar.

Representa um componente curricular (disciplina, atividade, etc.)
com todas suas características e regras de validação.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime

from ..value_objects.ValueObjects import (
    CodigoComponente, CargaHoraria, ExpressaoPreRequisito,
    TipoComponente, ModalidadeEducacao, NaturezaComponente
)
from ..exceptions.RadarExceptions import ComponenteCurricularInvalidoException


@dataclass
class ComponenteCurricular:
    """
    Entidade que representa um componente curricular.
    
    Pode ser uma disciplina, atividade, trabalho de conclusão, etc.
    Mantém informações sobre pré-requisitos, equivalências e cargas horárias.
    """
    
    # Identificador único
    id: UUID = field(default_factory=uuid4)
    
    # Dados obrigatórios
    codigo: CodigoComponente = field()
    nome: str = field()
    tipo: TipoComponente = field()
    modalidade: ModalidadeEducacao = field()
    carga_horaria: CargaHoraria = field()
    
    # Dados relacionais
    unidade_responsavel: str = field()
    pre_requisitos: ExpressaoPreRequisito = field(default_factory=lambda: ExpressaoPreRequisito(""))
    co_requisitos: ExpressaoPreRequisito = field(default_factory=lambda: ExpressaoPreRequisito(""))
    equivalencias: List[str] = field(default_factory=list)
    
    # Configurações
    matriculavel_online: bool = True
    horario_flexivel_turma: bool = False
    horario_flexivel_docente: bool = False
    obrigatoriedade_nota_final: bool = True
    pode_criar_turma_sem_solicitacao: bool = False
    necessita_orientador: bool = False
    possui_subturmas: bool = False
    exige_horario: bool = True
    permite_multiplas_aprovacoes: bool = False
    quantidade_avaliacoes: int = 1
    excluir_avaliacao_institucional: bool = False
    
    # Conteúdo
    ementa_descricao: Optional[str] = None
    
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
        if not self.nome.strip():
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Nome é obrigatório"
            )
        
        if len(self.nome.strip()) < 3:
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Nome deve ter pelo menos 3 caracteres"
            )
        
        if not self.unidade_responsavel.strip():
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Unidade responsável é obrigatória"
            )
    
    def _validar_regras_negocio(self) -> None:
        """Valida regras específicas de negócio."""
        # Validar quantidade de avaliações
        if self.quantidade_avaliacoes < 1 or self.quantidade_avaliacoes > 10:
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Quantidade de avaliações deve estar entre 1 e 10"
            )
        
        # Validar consistência de configurações
        if self.necessita_orientador and not self.permite_multiplas_aprovacoes:
            # Componentes que precisam de orientador geralmente permitem múltiplas aprovações
            pass  # Apenas log de warning, não erro
        
        # Validar equivalências (não podem incluir o próprio código)
        if str(self.codigo) in self.equivalencias:
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Componente não pode ser equivalente a si mesmo"
            )
    
    def obter_codigos_prerequisitos(self) -> Set[str]:
        """Obtém códigos de todos os pré-requisitos."""
        return self.pre_requisitos.obter_codigos_componentes()
    
    def obter_codigos_corequisitos(self) -> Set[str]:
        """Obtém códigos de todos os co-requisitos."""
        return self.co_requisitos.obter_codigos_componentes()
    
    def tem_prerequisitos(self) -> bool:
        """Verifica se o componente possui pré-requisitos."""
        return self.pre_requisitos.tem_prerequisitos
    
    def tem_corequisitos(self) -> bool:
        """Verifica se o componente possui co-requisitos."""
        return self.co_requisitos.tem_prerequisitos
    
    def adicionar_equivalencia(self, codigo_equivalente: str) -> None:
        """
        Adiciona uma equivalência ao componente.
        
        Args:
            codigo_equivalente: Código do componente equivalente
        """
        if codigo_equivalente == str(self.codigo):
            raise ComponenteCurricularInvalidoException(
                str(self.codigo),
                "Componente não pode ser equivalente a si mesmo"
            )
        
        if codigo_equivalente not in self.equivalencias:
            self.equivalencias.append(codigo_equivalente)
            self.atualizado_em = datetime.now()
    
    def remover_equivalencia(self, codigo_equivalente: str) -> None:
        """
        Remove uma equivalência do componente.
        
        Args:
            codigo_equivalente: Código do componente a ser removido
        """
        if codigo_equivalente in self.equivalencias:
            self.equivalencias.remove(codigo_equivalente)
            self.atualizado_em = datetime.now()
    
    def atualizar_ementa(self, nova_ementa: str) -> None:
        """
        Atualiza a ementa/descrição do componente.
        
        Args:
            nova_ementa: Nova ementa do componente
        """
        if nova_ementa and len(nova_ementa.strip()) > 0:
            self.ementa_descricao = nova_ementa.strip()
            self.atualizado_em = datetime.now()
    
    def atualizar_configuracoes(self, **kwargs) -> None:
        """
        Atualiza configurações específicas do componente.
        
        Args:
            **kwargs: Configurações a serem atualizadas
        """
        configuracoes_validas = {
            'matriculavel_online', 'horario_flexivel_turma', 'horario_flexivel_docente',
            'obrigatoriedade_nota_final', 'pode_criar_turma_sem_solicitacao',
            'necessita_orientador', 'possui_subturmas', 'exige_horario',
            'permite_multiplas_aprovacoes', 'quantidade_avaliacoes',
            'excluir_avaliacao_institucional'
        }
        
        for chave, valor in kwargs.items():
            if chave in configuracoes_validas:
                setattr(self, chave, valor)
        
        self.atualizado_em = datetime.now()
    
    @property
    def departamento(self) -> str:
        """Obtém o departamento do componente (a partir do código)."""
        return self.codigo.departamento
    
    @property
    def carga_horaria_total(self) -> int:
        """Obtém a carga horária total do componente."""
        return self.carga_horaria.total
    
    def __eq__(self, other) -> bool:
        """Componentes são iguais se têm o mesmo código."""
        if not isinstance(other, ComponenteCurricular):
            return False
        return self.codigo == other.codigo
    
    def __hash__(self) -> int:
        """Hash baseado no código do componente."""
        return hash(self.codigo)
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome} ({self.carga_horaria})"
    
    def __repr__(self) -> str:
        return f"ComponenteCurricular(codigo={self.codigo}, nome='{self.nome}')"