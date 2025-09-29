"""
Model SQLAlchemy para a entidade Curso.

Define a estrutura da tabela de cursos no banco de dados
usando SQLAlchemy ORM.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CursoModel(Base):
    """
    Model para representação de cursos no banco de dados.
    
    Mapeia a entidade Curso para estrutura relacional,
    incluindo campos de auditoria e metadados.
    """
    
    __tablename__ = 'cursos'
    
    # Chave primária
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Campos da entidade
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(500), nullable=False, index=True)
    unidade_vinculacao = Column(String(200), nullable=False, index=True)
    municipio_funcionamento = Column(String(100), nullable=False)
    modalidade = Column(String(50), nullable=False, index=True)
    turno = Column(String(50), nullable=False)
    grau_academico = Column(String(50), nullable=False)
    url_origem = Column(Text, nullable=True)
    
    # Campos de auditoria
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def __repr__(self):
        return f"<CursoModel(codigo='{self.codigo}', nome='{self.nome}')>"
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"