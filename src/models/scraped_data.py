"""
Modelos de dados para representar informações coletadas pelo web scraper.

Este módulo define as estruturas de dados que serão usadas para:
1. Armazenar dados coletados dos sites
2. Validar informações antes de enviar para a API
3. Padronizar formato de dados entre diferentes scrapers
"""
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ScrapingStatus(str, Enum):
    """Status do processo de scraping"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingType(str, Enum):
    """Tipos de scraping disponíveis"""
    COURSES = "courses"
    SYLLABI = "syllabi"
    SCHEDULES = "schedules"
    PROFESSORS = "professors"
    FULL_SYNC = "full_sync"


class BaseScrapedData(BaseModel):
    """Classe base para todos os dados coletados"""
    scraped_at: datetime = Field(default_factory=datetime.now)
    source_url: str
    scraper_version: str = "1.0.0"
    
    class Config:
        use_enum_values = True


class Course(BaseScrapedData):
    """Modelo para dados de curso coletados"""
    course_code: str = Field(..., description="Código da disciplina (ex: INF001)")
    course_name: str = Field(..., description="Nome da disciplina")
    credits: int = Field(..., ge=1, le=20, description="Número de créditos")
    workload: int = Field(..., ge=15, le=300, description="Carga horária em horas")
    department: str = Field(..., description="Departamento responsável")
    semester: Optional[int] = Field(None, ge=1, le=10, description="Semestre recomendado")
    prerequisites: List[str] = Field(default_factory=list, description="Códigos das disciplinas pré-requisitos")
    description: Optional[str] = Field(None, description="Descrição/ementa da disciplina")
    
    @validator('course_code')
    def validate_course_code(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Código do curso deve ter pelo menos 3 caracteres')
        return v.upper().strip()


class Schedule(BaseScrapedData):
    """Modelo para horários de turmas"""
    course_code: str
    class_code: str = Field(..., description="Código da turma (ex: T01, T02)")
    professor: str
    schedule_text: str = Field(..., description="Horário em formato texto (ex: 2M34, 4T56)")
    classroom: Optional[str] = Field(None, description="Sala de aula")
    semester: str = Field(..., description="Semestre letivo (ex: 2024/1)")
    max_students: Optional[int] = Field(None, ge=1, description="Número máximo de alunos")
    enrolled_students: Optional[int] = Field(None, ge=0, description="Alunos matriculados")
    
    # Campos processados (calculados a partir de schedule_text)
    days_of_week: List[int] = Field(default_factory=list, description="Dias da semana (1=segunda, 7=domingo)")
    start_time: Optional[time] = Field(None, description="Horário de início")
    end_time: Optional[time] = Field(None, description="Horário de término")


class Professor(BaseScrapedData):
    """Modelo para dados de professores"""
    name: str
    email: Optional[str] = Field(None)
    department: str
    courses_taught: List[str] = Field(default_factory=list, description="Códigos das disciplinas que leciona")
    research_areas: List[str] = Field(default_factory=list, description="Áreas de pesquisa")
    lattes_url: Optional[str] = Field(None, description="URL do currículo Lattes")


class SyllabusData(BaseScrapedData):
    """Modelo para dados extraídos de PDFs de ementa"""
    course_code: str
    course_name: str
    objectives: Optional[str] = Field(None, description="Objetivos da disciplina")
    syllabus_content: Optional[str] = Field(None, description="Conteúdo programático")
    methodology: Optional[str] = Field(None, description="Metodologia de ensino")
    evaluation_criteria: Optional[str] = Field(None, description="Critérios de avaliação")
    bibliography: List[str] = Field(default_factory=list, description="Bibliografia")
    competencies: List[str] = Field(default_factory=list, description="Competências desenvolvidas")
    pdf_url: str = Field(..., description="URL do PDF original")
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confiança na extração (0-1)")


class ScrapingJob(BaseModel):
    """Modelo para jobs de scraping"""
    job_id: str
    scraping_type: ScrapingType
    status: ScrapingStatus = ScrapingStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: int = Field(0, ge=0, le=100, description="Progresso em percentual")
    results_count: int = Field(0, ge=0, description="Número de itens coletados")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configurações específicas do job")
    
    @property
    def duration(self) -> Optional[int]:
        """Duração do job em segundos"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


class ScrapingResult(BaseModel):
    """Resultado completo de um processo de scraping"""
    job: ScrapingJob
    data: List[BaseScrapedData] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso do scraping"""
        if not self.data:
            return 0.0
        # Aqui você pode implementar lógica específica de validação
        return float(len(self.data)) / max(self.job.results_count, 1)


# Tipos de união para facilitar o uso
ScrapedDataType = Course | Schedule | Professor | SyllabusData