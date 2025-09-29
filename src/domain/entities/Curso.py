"""
Entidade Curso do domínio Radar.

Representa um curso de graduação com todas suas características
e regras de negócio específicas.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..value_objects.ValueObjects import (
    CodigoCurso, NomeCurso, AnoPeriodo, SituacaoEstrutura,
    PrazoConclusao, CargaHoraria
)
from ..exceptions.RadarExceptions import CursoInvalidoException


@dataclass
class Curso:
    """
    Entidade que representa um curso de graduação.
    
    Agrega informações sobre o curso e suas estruturas curriculares,
    mantendo a consistência das regras de negócio.
    """
    
    # Identificador único
    id: UUID = field(default_factory=uuid4)
    
    # Dados obrigatórios
    codigo: CodigoCurso = field()
    nome: NomeCurso = field()
    unidade_vinculacao: str = field()
    municipio_funcionamento: str = field()
    
    # Dados opcionais
    modalidade: Optional[str] = None
    turno: Optional[str] = None
    grau_academico: str = "BACHARELADO"
    
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
        if not self.unidade_vinculacao.strip():
            raise CursoInvalidoException(
                str(self.codigo), 
                "Unidade de vinculação é obrigatória"
            )
        
        if not self.municipio_funcionamento.strip():
            raise CursoInvalidoException(
                str(self.codigo),
                "Município de funcionamento é obrigatório"
            )
    
    def _validar_regras_negocio(self) -> None:
        """Valida regras específicas de negócio."""
        # Validar grau acadêmico
        graus_validos = ["BACHARELADO", "LICENCIATURA", "TECNÓLOGO"]
        if self.grau_academico not in graus_validos:
            raise CursoInvalidoException(
                str(self.codigo),
                f"Grau acadêmico inválido: {self.grau_academico}"
            )
    
    def atualizar_informacoes(self, 
                            nome: Optional[NomeCurso] = None,
                            unidade_vinculacao: Optional[str] = None,
                            municipio_funcionamento: Optional[str] = None,
                            modalidade: Optional[str] = None,
                            turno: Optional[str] = None) -> None:
        """
        Atualiza informações do curso mantendo integridade.
        
        Args:
            nome: Novo nome do curso
            unidade_vinculacao: Nova unidade de vinculação  
            municipio_funcionamento: Novo município
            modalidade: Nova modalidade
            turno: Novo turno
        """
        if nome is not None:
            self.nome = nome
        
        if unidade_vinculacao is not None:
            if not unidade_vinculacao.strip():
                raise CursoInvalidoException(
                    str(self.codigo),
                    "Unidade de vinculação não pode ser vazia"
                )
            self.unidade_vinculacao = unidade_vinculacao.strip()
        
        if municipio_funcionamento is not None:
            if not municipio_funcionamento.strip():
                raise CursoInvalidoException(
                    str(self.codigo),
                    "Município não pode ser vazio"
                )
            self.municipio_funcionamento = municipio_funcionamento.strip()
        
        if modalidade is not None:
            self.modalidade = modalidade
        
        if turno is not None:
            self.turno = turno
        
        self.atualizado_em = datetime.now()
    
    def __eq__(self, other) -> bool:
        """Cursos são iguais se têm o mesmo código."""
        if not isinstance(other, Curso):
            return False
        return self.codigo == other.codigo
    
    def __hash__(self) -> int:
        """Hash baseado no código do curso."""
        return hash(self.codigo)
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
    
    def __repr__(self) -> str:
        return f"Curso(codigo={self.codigo}, nome='{self.nome}')"