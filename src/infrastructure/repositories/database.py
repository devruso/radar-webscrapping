"""
Configuração e gerenciamento de conexões com banco de dados.

Fornece classes e utilitários para gerenciar conexões assíncronas
com banco de dados usando SQLAlchemy.
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from ...shared.logging import get_logger

logger = get_logger(__name__)


class AsyncDatabaseSession:
    """
    Gerenciador de sessões assíncronas de banco de dados.
    
    Fornece interface para obter sessões de banco configuradas
    e gerenciar o ciclo de vida das conexões.
    """
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Inicializa o gerenciador de sessões.
        
        Args:
            database_url: URL de conexão com o banco
            echo: Se deve fazer log das queries SQL
        """
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_factory = None
    
    def initialize(self) -> None:
        """Inicializa engine e factory de sessões."""
        try:
            # Configurações específicas para SQLite assíncrono
            if self.database_url.startswith('sqlite'):
                connect_args = {
                    "check_same_thread": False,
                }
                poolclass = StaticPool
            else:
                connect_args = {}
                poolclass = None
            
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                connect_args=connect_args,
                poolclass=poolclass,
                future=True
            )
            
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info(f"Banco de dados inicializado: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager para obter sessão de banco.
        
        Yields:
            Sessão assíncrona configurada
        """
        if not self._session_factory:
            raise RuntimeError("Database não foi inicializado. Chame initialize() primeiro.")
        
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Erro na sessão de banco, rollback executado: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Fecha todas as conexões do engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Conexões do banco de dados fechadas")
    
    @property
    def engine(self):
        """Retorna o engine de banco de dados."""
        return self._engine


class DatabaseConfig:
    """
    Configuração centralizada de banco de dados.
    
    Fornece configurações padrão e utilitários para
    diferentes ambientes (desenvolvimento, teste, produção).
    """
    
    @staticmethod
    def get_sqlite_url(db_path: str = "data/radar_webscrapping.db") -> str:
        """
        Gera URL para banco SQLite assíncrono.
        
        Args:
            db_path: Caminho para o arquivo do banco
            
        Returns:
            URL de conexão SQLite assíncrona
        """
        return f"sqlite+aiosqlite:///{db_path}"
    
    @staticmethod
    def get_postgres_url(
        host: str = "localhost",
        port: int = 5432,
        database: str = "radar_webscrapping",
        username: str = "radar",
        password: str = "radar123"
    ) -> str:
        """
        Gera URL para banco PostgreSQL assíncrono.
        
        Args:
            host: Host do banco
            port: Porta do banco
            database: Nome do banco
            username: Usuário
            password: Senha
            
        Returns:
            URL de conexão PostgreSQL assíncrona
        """
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def create_development_session() -> AsyncDatabaseSession:
        """
        Cria sessão para ambiente de desenvolvimento.
        
        Returns:
            Sessão configurada para desenvolvimento
        """
        db_url = DatabaseConfig.get_sqlite_url("data/dev_radar.db")
        session = AsyncDatabaseSession(db_url, echo=True)
        session.initialize()
        return session
    
    @staticmethod
    def create_test_session() -> AsyncDatabaseSession:
        """
        Cria sessão para ambiente de testes.
        
        Returns:
            Sessão configurada para testes
        """
        db_url = DatabaseConfig.get_sqlite_url(":memory:")
        session = AsyncDatabaseSession(db_url, echo=False)
        session.initialize()
        return session
    
    @staticmethod
    def create_production_session(database_url: str) -> AsyncDatabaseSession:
        """
        Cria sessão para ambiente de produção.
        
        Args:
            database_url: URL do banco de produção
            
        Returns:
            Sessão configurada para produção
        """
        session = AsyncDatabaseSession(database_url, echo=False)
        session.initialize()
        return session


# Instância global para uso simples
_global_session: Optional[AsyncDatabaseSession] = None


def get_database_session() -> AsyncDatabaseSession:
    """
    Obtém sessão global de banco de dados.
    
    Returns:
        Sessão de banco configurada
    """
    global _global_session
    
    if _global_session is None:
        _global_session = DatabaseConfig.create_development_session()
    
    return _global_session


async def initialize_database() -> None:
    """Inicializa banco de dados global."""
    session = get_database_session()
    # Aqui poderia executar migrations, criar tabelas, etc.
    logger.info("Banco de dados global inicializado")


async def close_database() -> None:
    """Fecha conexões do banco de dados global."""
    global _global_session
    
    if _global_session:
        await _global_session.close()
        _global_session = None
        logger.info("Banco de dados global fechado")