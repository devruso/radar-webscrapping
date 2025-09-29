"""
Models SQLAlchemy para as entidades do domínio.

Contém as definições de tabelas e relacionamentos do banco de dados
usando SQLAlchemy ORM.
"""

from .CursoModel import CursoModel

__all__ = [
    'CursoModel'
]