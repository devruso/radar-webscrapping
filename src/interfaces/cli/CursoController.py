"""
Controller CLI para operações de scraping de cursos.

Fornece interface de linha de comando para executar
operações de scraping seguindo Clean Architecture.
"""

import asyncio
import click
import json
from typing import Optional
from datetime import datetime

from ...application.use_cases import ScrapearCursosUseCase
from ...application.dtos.DataTransferObjects import ConfiguracaoScrapingDto
from ...infrastructure.repositories.SqlAlchemyCursoRepository import SqlAlchemyCursoRepository
from ...infrastructure.scrapers.SigaaUfbaCursoScraper import SigaaUfbaCursoScraper
from ...infrastructure.api_clients.RadarApiClient import RadarApiClient
from ...infrastructure.repositories.database import get_database_session
from ...shared.logging import get_logger, configure_logging

logger = get_logger(__name__)


class CursoScrapingController:
    """
    Controller para operações de scraping de cursos.
    
    Orquestra a configuração de dependências e execução
    de casos de uso relacionados a scraping de cursos.
    """
    
    def __init__(self):
        """Inicializa o controller com dependências."""
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        """Configura injeção de dependências."""
        # Database
        self._db_session = get_database_session()
        
        # Repositories
        self._curso_repository = SqlAlchemyCursoRepository(self._db_session)
        
        # External Services
        self._scraping_service = SigaaUfbaCursoScraper()
        self._api_client = RadarApiClient()
        
        # Use Cases
        self._scraping_use_case = ScrapearCursosUseCase(
            self._curso_repository,
            self._scraping_service,
            self._api_client
        )
    
    async def executar_scraping_completo(self,
                                       unidade_filtro: Optional[str] = None,
                                       modalidade_filtro: Optional[str] = None,
                                       sincronizar: bool = True) -> dict:
        """
        Executa scraping completo de cursos.
        
        Args:
            unidade_filtro: Filtrar por unidade específica
            modalidade_filtro: Filtrar por modalidade específica
            sincronizar: Se deve sincronizar com backend
            
        Returns:
            Resultado do scraping em formato dicionário
        """
        try:
            logger.info("Iniciando scraping completo de cursos via CLI")
            
            # Configurar scraping
            configuracao = ConfiguracaoScrapingDto(
                incluir_cursos=True,
                incluir_componentes=False,
                incluir_estruturas=False,
                filtro_unidade=unidade_filtro,
                filtro_modalidade=modalidade_filtro,
                incluir_pre_requisitos=False,
                incluir_equivalencias=False,
                incluir_estruturas_historicas=False
            )
            
            # Executar scraping
            resultado = await self._scraping_use_case.executar(
                configuracao, sincronizar
            )
            
            logger.info(f"Scraping concluído - Job {resultado.id}")
            
            return {
                "sucesso": True,
                "job_id": resultado.id,
                "status": resultado.status.value,
                "itens_coletados": resultado.itens_coletados,
                "duracao": str(resultado.concluido_em - resultado.iniciado_em) if resultado.concluido_em else None,
                "erros": resultado.erros
            }
            
        except Exception as e:
            logger.error(f"Erro no scraping de cursos: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def buscar_curso_especifico(self, codigo_curso: str) -> dict:
        """
        Busca um curso específico.
        
        Args:
            codigo_curso: Código do curso a ser buscado
            
        Returns:
            Dados do curso ou erro
        """
        try:
            logger.info(f"Buscando curso específico: {codigo_curso}")
            
            curso_dto = await self._scraping_use_case.obter_curso_especifico(codigo_curso)
            
            if curso_dto:
                return {
                    "sucesso": True,
                    "curso": {
                        "codigo": curso_dto.codigo,
                        "nome": curso_dto.nome,
                        "unidade": curso_dto.unidade_vinculacao,
                        "municipio": curso_dto.municipio_funcionamento,
                        "modalidade": curso_dto.modalidade,
                        "turno": curso_dto.turno,
                        "grau": curso_dto.grau_academico
                    }
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Curso {codigo_curso} não encontrado"
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar curso {codigo_curso}: {e}")
            return {
                "sucesso": False,
                "erro": str(e)
            }
    
    async def listar_cursos_coletados(self, filtro_unidade: Optional[str] = None) -> dict:
        """
        Lista cursos já coletados.
        
        Args:
            filtro_unidade: Filtrar por unidade específica
            
        Returns:
            Lista de cursos coletados
        """
        try:
            logger.info("Listando cursos coletados")
            
            cursos_dto = await self._scraping_use_case.listar_cursos_coletados(filtro_unidade)
            
            cursos_data = []
            for curso in cursos_dto:
                cursos_data.append({
                    "codigo": curso.codigo,
                    "nome": curso.nome,
                    "unidade": curso.unidade_vinculacao,
                    "modalidade": curso.modalidade,
                    "turno": curso.turno
                })
            
            return {
                "sucesso": True,
                "total": len(cursos_data),
                "cursos": cursos_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar cursos: {e}")
            return {
                "sucesso": False,
                "erro": str(e)
            }


# Comandos CLI usando Click

@click.group()
@click.option('--log-level', default='INFO', help='Nível de log (DEBUG, INFO, WARNING, ERROR)')
@click.option('--log-format', default='detailed', help='Formato do log (simple, detailed, json)')
def cli(log_level: str, log_format: str):
    """Interface CLI para scraping de cursos do SIGAA UFBA."""
    configure_logging(log_level, log_format)


@cli.command()
@click.option('--unidade', '-u', help='Filtrar por unidade específica')
@click.option('--modalidade', '-m', help='Filtrar por modalidade específica')
@click.option('--no-sync', is_flag=True, help='Não sincronizar com backend')
@click.option('--output', '-o', help='Arquivo para salvar resultado JSON')
def scrape_cursos(unidade: Optional[str], 
                 modalidade: Optional[str], 
                 no_sync: bool,
                 output: Optional[str]):
    """Executa scraping completo de cursos."""
    async def _execute():
        controller = CursoScrapingController()
        resultado = await controller.executar_scraping_completo(
            unidade, modalidade, not no_sync
        )
        
        # Output do resultado
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            click.echo(f"Resultado salvo em: {output}")
        else:
            click.echo(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    asyncio.run(_execute())


@cli.command()
@click.argument('codigo_curso')
def buscar_curso(codigo_curso: str):
    """Busca um curso específico pelo código."""
    async def _execute():
        controller = CursoScrapingController()
        resultado = await controller.buscar_curso_especifico(codigo_curso)
        click.echo(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    asyncio.run(_execute())


@cli.command()
@click.option('--unidade', '-u', help='Filtrar por unidade específica')
@click.option('--output', '-o', help='Arquivo para salvar lista JSON')
def listar_cursos(unidade: Optional[str], output: Optional[str]):
    """Lista cursos já coletados e armazenados."""
    async def _execute():
        controller = CursoScrapingController()
        resultado = await controller.listar_cursos_coletados(unidade)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            click.echo(f"Lista salva em: {output}")
        else:
            click.echo(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    asyncio.run(_execute())


@cli.command()
def status():
    """Mostra status do sistema de scraping."""
    async def _execute():
        try:
            controller = CursoScrapingController()
            # Testar conectividade
            configuracao_teste = ConfiguracaoScrapingDto(
                incluir_cursos=True,
                incluir_componentes=False,
                incluir_estruturas=False
            )
            
            # Status básico
            status_info = {
                "sistema": "Radar WebScrapping - Cursos",
                "timestamp": datetime.now().isoformat(),
                "versao": "1.0.0",
                "ambiente": "desenvolvimento",
                "status": "online"
            }
            
            click.echo(json.dumps(status_info, indent=2, ensure_ascii=False))
            
        except Exception as e:
            error_info = {
                "sistema": "Radar WebScrapping - Cursos",
                "status": "erro",
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
            click.echo(json.dumps(error_info, indent=2, ensure_ascii=False))
    
    asyncio.run(_execute())


if __name__ == '__main__':
    cli()