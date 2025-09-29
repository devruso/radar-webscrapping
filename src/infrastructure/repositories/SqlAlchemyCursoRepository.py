"""
Implementação concreta do repositório de cursos usando SQLAlchemy.

Implementa a interface ICursoRepository para persistência
de dados de cursos em banco de dados relacional.
"""

from typing import List, Optional
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ...application.interfaces.ICursoRepository import ICursoRepository
from ...domain.entities import Curso
from ...domain.value_objects import CodigoCurso
from ...domain.exceptions import RepositoryException, EntityNotFoundException
from ...shared.logging import get_logger
from .models.CursoModel import CursoModel
from .database import AsyncDatabaseSession

logger = get_logger(__name__)


class SqlAlchemyCursoRepository(ICursoRepository):
    """
    Repositório concreto para cursos usando SQLAlchemy.
    
    Implementa operações de persistência para entidades Curso
    usando SQLAlchemy ORM com suporte assíncrono.
    """
    
    def __init__(self, db_session: AsyncDatabaseSession):
        """
        Inicializa o repositório.
        
        Args:
            db_session: Sessão de banco de dados assíncrona
        """
        self._db_session = db_session
    
    async def salvar(self, curso: Curso) -> None:
        """
        Salva um curso no banco de dados.
        
        Args:
            curso: Curso a ser salvo
            
        Raises:
            RepositoryException: Em caso de erro na persistência
        """
        try:
            async with self._db_session.get_session() as session:
                # Verificar se curso já existe
                curso_existente = await self._buscar_model_por_codigo(session, str(curso.codigo))
                
                if curso_existente:
                    # Atualizar curso existente
                    await self._atualizar_model(session, curso_existente, curso)
                    logger.debug(f"Curso {curso.codigo} atualizado")
                else:
                    # Criar novo curso
                    curso_model = self._criar_model_do_curso(curso)
                    session.add(curso_model)
                    logger.debug(f"Curso {curso.codigo} criado")
                
                await session.commit()
                logger.info(f"Curso {curso.codigo} salvo com sucesso")
                
        except IntegrityError as e:
            logger.error(f"Erro de integridade ao salvar curso {curso.codigo}: {e}")
            raise RepositoryException(f"Violação de integridade: {e}")
        
        except SQLAlchemyError as e:
            logger.error(f"Erro SQLAlchemy ao salvar curso {curso.codigo}: {e}")
            raise RepositoryException(f"Erro de banco de dados: {e}")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar curso {curso.codigo}: {e}")
            raise RepositoryException(f"Erro inesperado: {e}")
    
    async def buscar_por_codigo(self, codigo: str) -> Optional[Curso]:
        """
        Busca um curso pelo código.
        
        Args:
            codigo: Código do curso
            
        Returns:
            Curso encontrado ou None
        """
        try:
            async with self._db_session.get_session() as session:
                curso_model = await self._buscar_model_por_codigo(session, codigo)
                
                if curso_model:
                    curso = self._criar_curso_do_model(curso_model)
                    logger.debug(f"Curso {codigo} encontrado")
                    return curso
                
                logger.debug(f"Curso {codigo} não encontrado")
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar curso {codigo}: {e}")
            raise RepositoryException(f"Erro na busca: {e}")
    
    async def listar_todos(self) -> List[Curso]:
        """
        Lista todos os cursos.
        
        Returns:
            Lista com todos os cursos
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = select(CursoModel).order_by(CursoModel.codigo)
                result = await session.execute(stmt)
                curso_models = result.scalars().all()
                
                cursos = [self._criar_curso_do_model(model) for model in curso_models]
                
                logger.info(f"Listados {len(cursos)} cursos")
                return cursos
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao listar cursos: {e}")
            raise RepositoryException(f"Erro na listagem: {e}")
    
    async def listar_por_unidade(self, unidade: str) -> List[Curso]:
        """
        Lista cursos por unidade de vinculação.
        
        Args:
            unidade: Nome da unidade de vinculação
            
        Returns:
            Lista de cursos da unidade
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = select(CursoModel).where(
                    CursoModel.unidade_vinculacao.ilike(f"%{unidade}%")
                ).order_by(CursoModel.nome)
                
                result = await session.execute(stmt)
                curso_models = result.scalars().all()
                
                cursos = [self._criar_curso_do_model(model) for model in curso_models]
                
                logger.info(f"Encontrados {len(cursos)} cursos da unidade {unidade}")
                return cursos
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao listar cursos por unidade {unidade}: {e}")
            raise RepositoryException(f"Erro na busca por unidade: {e}")
    
    async def listar_por_modalidade(self, modalidade: str) -> List[Curso]:
        """
        Lista cursos por modalidade.
        
        Args:
            modalidade: Modalidade do curso
            
        Returns:
            Lista de cursos da modalidade
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = select(CursoModel).where(
                    CursoModel.modalidade.ilike(f"%{modalidade}%")
                ).order_by(CursoModel.nome)
                
                result = await session.execute(stmt)
                curso_models = result.scalars().all()
                
                cursos = [self._criar_curso_do_model(model) for model in curso_models]
                
                logger.info(f"Encontrados {len(cursos)} cursos da modalidade {modalidade}")
                return cursos
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao listar cursos por modalidade {modalidade}: {e}")
            raise RepositoryException(f"Erro na busca por modalidade: {e}")
    
    async def atualizar(self, curso: Curso) -> None:
        """
        Atualiza um curso existente.
        
        Args:
            curso: Curso a ser atualizado
            
        Raises:
            EntityNotFoundException: Se o curso não for encontrado
            RepositoryException: Em caso de erro na atualização
        """
        try:
            async with self._db_session.get_session() as session:
                curso_model = await self._buscar_model_por_codigo(session, str(curso.codigo))
                
                if not curso_model:
                    raise EntityNotFoundException(f"Curso {curso.codigo} não encontrado para atualização")
                
                await self._atualizar_model(session, curso_model, curso)
                await session.commit()
                
                logger.info(f"Curso {curso.codigo} atualizado com sucesso")
                
        except EntityNotFoundException:
            raise
        
        except SQLAlchemyError as e:
            logger.error(f"Erro ao atualizar curso {curso.codigo}: {e}")
            raise RepositoryException(f"Erro na atualização: {e}")
    
    async def remover(self, codigo: str) -> bool:
        """
        Remove um curso.
        
        Args:
            codigo: Código do curso a ser removido
            
        Returns:
            True se removido com sucesso, False se não encontrado
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = delete(CursoModel).where(CursoModel.codigo == codigo)
                result = await session.execute(stmt)
                await session.commit()
                
                removido = result.rowcount > 0
                
                if removido:
                    logger.info(f"Curso {codigo} removido com sucesso")
                else:
                    logger.warning(f"Curso {codigo} não encontrado para remoção")
                
                return removido
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao remover curso {codigo}: {e}")
            raise RepositoryException(f"Erro na remoção: {e}")
    
    async def existe(self, codigo: str) -> bool:
        """
        Verifica se um curso existe.
        
        Args:
            codigo: Código do curso
            
        Returns:
            True se existe, False caso contrário
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = select(func.count(CursoModel.id)).where(CursoModel.codigo == codigo)
                result = await session.execute(stmt)
                count = result.scalar()
                
                existe = count > 0
                logger.debug(f"Curso {codigo} existe: {existe}")
                return existe
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao verificar existência do curso {codigo}: {e}")
            raise RepositoryException(f"Erro na verificação: {e}")
    
    async def contar(self) -> int:
        """
        Conta o total de cursos.
        
        Returns:
            Número total de cursos
        """
        try:
            async with self._db_session.get_session() as session:
                stmt = select(func.count(CursoModel.id))
                result = await session.execute(stmt)
                count = result.scalar()
                
                logger.debug(f"Total de cursos: {count}")
                return count
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao contar cursos: {e}")
            raise RepositoryException(f"Erro na contagem: {e}")
    
    async def _buscar_model_por_codigo(self, session: AsyncSession, codigo: str) -> Optional[CursoModel]:
        """Busca model do curso por código."""
        stmt = select(CursoModel).where(CursoModel.codigo == codigo)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _criar_model_do_curso(self, curso: Curso) -> CursoModel:
        """Cria model SQLAlchemy a partir da entidade."""
        return CursoModel(
            codigo=str(curso.codigo),
            nome=str(curso.nome),
            unidade_vinculacao=curso.unidade_vinculacao,
            municipio_funcionamento=curso.municipio_funcionamento,
            modalidade=curso.modalidade,
            turno=curso.turno,
            grau_academico=curso.grau_academico,
            url_origem=curso.url_origem,
            criado_em=datetime.now(),
            atualizado_em=datetime.now()
        )
    
    def _criar_curso_do_model(self, model: CursoModel) -> Curso:
        """Cria entidade a partir do model SQLAlchemy."""
        return Curso(
            codigo=CodigoCurso(model.codigo),
            nome=model.nome,
            unidade_vinculacao=model.unidade_vinculacao,
            municipio_funcionamento=model.municipio_funcionamento,
            modalidade=model.modalidade,
            turno=model.turno,
            grau_academico=model.grau_academico,
            url_origem=model.url_origem
        )
    
    async def _atualizar_model(self, session: AsyncSession, model: CursoModel, curso: Curso) -> None:
        """Atualiza model com dados da entidade."""
        model.nome = str(curso.nome)
        model.unidade_vinculacao = curso.unidade_vinculacao
        model.municipio_funcionamento = curso.municipio_funcionamento
        model.modalidade = curso.modalidade
        model.turno = curso.turno
        model.grau_academico = curso.grau_academico
        model.url_origem = curso.url_origem
        model.atualizado_em = datetime.now()