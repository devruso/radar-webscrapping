"""
DTOs (Data Transfer Objects) para comunicação entre camadas.

Os DTOs servem para transportar dados entre camadas sem expor
as entidades de domínio diretamente às camadas externas.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StatusJobDto(Enum):
    """Status de um job de scraping."""
    PENDENTE = "pendente"
    EXECUTANDO = "executando"
    CONCLUIDO = "concluido"
    ERRO = "erro"
    CANCELADO = "cancelado"


@dataclass
class CursoDto:
    """DTO para transferência de dados de curso."""
    codigo: str
    nome: str
    unidade_vinculacao: str
    municipio_funcionamento: str
    modalidade: Optional[str] = None
    turno: Optional[str] = None
    grau_academico: str = "BACHARELADO"
    url_origem: Optional[str] = None


@dataclass
class ComponenteCurricularDto:
    """DTO para transferência de dados de componente curricular."""
    codigo: str
    nome: str
    tipo: str
    modalidade: str
    carga_horaria_total: int
    unidade_responsavel: str
    pre_requisitos: str = ""
    co_requisitos: str = ""
    equivalencias: List[str] = None
    ementa_descricao: Optional[str] = None
    matriculavel_online: bool = True
    url_origem: Optional[str] = None
    
    def __post_init__(self):
        if self.equivalencias is None:
            self.equivalencias = []


@dataclass
class ComponenteEstruturaDto:
    """DTO para componente dentro de uma estrutura curricular."""
    codigo_componente: str
    periodo_sugerido: int
    natureza: str
    carga_horaria_total: int


@dataclass
class EstruturaCurricularDto:
    """DTO para transferência de dados de estrutura curricular."""
    codigo: str
    codigo_curso: str
    matriz_curricular: str
    ano_periodo_vigencia: str
    situacao: str
    unidade_vinculacao: str
    municipio_funcionamento: str
    prazo_minimo: int
    prazo_medio: int
    prazo_maximo: int
    carga_horaria_obrigatoria: int
    carga_horaria_optativa: int
    carga_horaria_complementar: int
    carga_horaria_optativa_livre: int = 0
    componentes_por_periodo: Dict[int, List[ComponenteEstruturaDto]] = None
    url_origem: Optional[str] = None
    
    def __post_init__(self):
        if self.componentes_por_periodo is None:
            self.componentes_por_periodo = {}


@dataclass
class ConfiguracaoScrapingDto:
    """DTO para configurações de scraping."""
    url_base: Optional[str] = None
    filtro_unidade: Optional[str] = None
    filtro_modalidade: Optional[str] = None
    filtro_nome: Optional[str] = None
    filtro_departamento: Optional[str] = None
    filtro_tipo: Optional[str] = None
    codigo_curso: Optional[str] = None
    timeout_pagina: int = 30
    delay_entre_requests: float = 1.0
    max_tentativas: int = 3
    salvar_html_debug: bool = False
    modo_headless: bool = True


@dataclass
class JobScrapingDto:
    """DTO para job de scraping."""
    id: str
    tipo_scraping: str
    status: StatusJobDto
    configuracao: ConfiguracaoScrapingDto
    iniciado_em: datetime
    concluido_em: Optional[datetime] = None
    itens_coletados: int = 0
    erros: List[str] = None
    detalhes: Optional[str] = None
    
    def __post_init__(self):
        if self.erros is None:
            self.erros = []


@dataclass
class ResultadoScrapingDto:
    """DTO para resultado de scraping."""
    job_id: str
    tipo_scraping: str
    status: StatusJobDto
    cursos: List[CursoDto] = None
    componentes: List[ComponenteCurricularDto] = None
    estruturas: List[EstruturaCurricularDto] = None
    tempo_execucao_segundos: float = 0.0
    estatisticas: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cursos is None:
            self.cursos = []
        if self.componentes is None:
            self.componentes = []
        if self.estruturas is None:
            self.estruturas = []
        if self.estatisticas is None:
            self.estatisticas = {}


@dataclass
class SincronizacaoDto:
    """DTO para resultado de sincronização com backend."""
    tipo_dados: str
    status: str
    itens_enviados: int
    itens_processados: int
    itens_com_erro: int
    tempo_execucao_segundos: float
    detalhes_erro: Optional[str] = None
    

@dataclass
class EstatisticasScrapingDto:
    """DTO para estatísticas de scraping."""
    total_jobs_executados: int
    jobs_em_andamento: int
    total_cursos_coletados: int
    total_componentes_coletados: int
    total_estruturas_coletadas: int
    tempo_medio_execucao: float
    taxa_sucesso: float
    ultima_execucao: Optional[datetime] = None


@dataclass
class HealthCheckDto:
    """DTO para health check do sistema."""
    status: str
    timestamp: datetime
    componentes: Dict[str, str]
    detalhes: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.detalhes is None:
            self.detalhes = {}


# Funções de conversão (mappers)

def curso_para_dto(curso) -> CursoDto:
    """Converte entidade Curso para DTO."""
    return CursoDto(
        codigo=str(curso.codigo),
        nome=str(curso.nome),
        unidade_vinculacao=curso.unidade_vinculacao,
        municipio_funcionamento=curso.municipio_funcionamento,
        modalidade=curso.modalidade,
        turno=curso.turno,
        grau_academico=curso.grau_academico,
        url_origem=curso.url_origem
    )


@dataclass
class ResultadoScrapingCompletoDto:
    """
    DTO para resultado de scraping completo.
    
    Consolida resultados de todos os tipos de scraping
    em uma única estrutura.
    """
    id_sessao: str
    tipo_execucao: str
    configuracao: ConfiguracaoScrapingDto
    iniciado_em: datetime
    concluido_em: Optional[datetime] = None
    sucesso_total: bool = False
    total_itens_coletados: int = 0
    erro_geral: Optional[str] = None
    
    # Jobs individuais
    job_cursos: Optional[JobScrapingDto] = None
    job_componentes: Optional[JobScrapingDto] = None
    job_estruturas: Optional[JobScrapingDto] = None
    
    def duracao_total(self) -> Optional[float]:
        """Calcula duração total em segundos."""
        if self.concluido_em and self.iniciado_em:
            return (self.concluido_em - self.iniciado_em).total_seconds()
        return None
    
    def resumo_execucao(self) -> Dict[str, Any]:
        """Retorna resumo da execução."""
        return {
            "id_sessao": self.id_sessao,
            "tipo_execucao": self.tipo_execucao,
            "sucesso_total": self.sucesso_total,
            "duracao_segundos": self.duracao_total(),
            "total_itens": self.total_itens_coletados,
            "jobs_executados": {
                "cursos": self.job_cursos is not None,
                "componentes": self.job_componentes is not None,
                "estruturas": self.job_estruturas is not None
            },
            "erro": self.erro_geral
        }


def componente_para_dto(componente) -> ComponenteCurricularDto:
    """Converte entidade ComponenteCurricular para DTO."""
    return ComponenteCurricularDto(
        codigo=str(componente.codigo),
        nome=componente.nome,
        tipo=componente.tipo.value,
        modalidade=componente.modalidade.value,
        carga_horaria_total=componente.carga_horaria.total,
        unidade_responsavel=componente.unidade_responsavel,
        pre_requisitos=str(componente.pre_requisitos),
        co_requisitos=str(componente.co_requisitos),
        equivalencias=componente.equivalencias.copy(),
        ementa_descricao=componente.ementa_descricao,
        matriculavel_online=componente.matriculavel_online,
        url_origem=componente.url_origem
    )


def estrutura_para_dto(estrutura) -> EstruturaCurricularDto:
    """Converte entidade EstruturaCurricular para DTO."""
    componentes_dto = {}
    for periodo, componentes in estrutura.componentes_por_periodo.items():
        componentes_dto[periodo] = [
            ComponenteEstruturaDto(
                codigo_componente=comp.codigo_componente,
                periodo_sugerido=comp.periodo_sugerido,
                natureza=comp.natureza.value,
                carga_horaria_total=comp.carga_horaria.total
            ) for comp in componentes
        ]
    
    return EstruturaCurricularDto(
        codigo=estrutura.codigo,
        codigo_curso=str(estrutura.codigo_curso),
        matriz_curricular=estrutura.matriz_curricular,
        ano_periodo_vigencia=str(estrutura.ano_periodo_vigencia),
        situacao=estrutura.situacao.value,
        unidade_vinculacao=estrutura.unidade_vinculacao,
        municipio_funcionamento=estrutura.municipio_funcionamento,
        prazo_minimo=estrutura.prazos_conclusao.minimo,
        prazo_medio=estrutura.prazos_conclusao.medio,
        prazo_maximo=estrutura.prazos_conclusao.maximo,
        carga_horaria_obrigatoria=estrutura.carga_horaria_obrigatoria,
        carga_horaria_optativa=estrutura.carga_horaria_optativa,
        carga_horaria_complementar=estrutura.carga_horaria_complementar,
        carga_horaria_optativa_livre=estrutura.carga_horaria_optativa_livre,
        componentes_por_periodo=componentes_dto,
        url_origem=estrutura.url_origem
    )