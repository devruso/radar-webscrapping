"""
Caso de uso para scraping de cursos.

Implementa a lógica de negócio para coleta de dados de cursos
do SIGAA, incluindo validação e persistência.
"""

from typing import List, Optional
import asyncio
from datetime import datetime

from ..interfaces.ICursoRepository import ICursoRepository
from ..interfaces.IScrapingService import ICursoScrapingService
from ..interfaces.IRadarApiClient import IRadarApiClient
from ..dtos.DataTransferObjects import (
    CursoDto, ConfiguracaoScrapingDto, JobScrapingDto, 
    StatusJobDto, curso_para_dto
)
from ...domain.entities import Curso
from ...domain.exceptions import ScrapingException, ValidationException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class ScrapearCursosUseCase:
    """
    Caso de uso para scraping de cursos.
    
    Coordena o processo completo de coleta, validação e persistência
    de dados de cursos do SIGAA.
    """
    
    def __init__(self,
                 curso_repository: ICursoRepository,
                 scraping_service: ICursoScrapingService,
                 api_client: IRadarApiClient):
        self._curso_repository = curso_repository
        self._scraping_service = scraping_service
        self._api_client = api_client
    
    async def executar(self, 
                      configuracao: ConfiguracaoScrapingDto,
                      sincronizar_backend: bool = True) -> JobScrapingDto:
        """
        Executa o scraping de cursos.
        
        Args:
            configuracao: Parâmetros de configuração do scraping
            sincronizar_backend: Se deve sincronizar com o backend
            
        Returns:
            Resultado do job de scraping
        """
        job = JobScrapingDto(
            id=self._gerar_job_id(),
            tipo_scraping="cursos",
            status=StatusJobDto.PENDENTE,
            configuracao=configuracao,
            iniciado_em=datetime.now()
        )
        
        try:
            logger.info(f"Iniciando scraping de cursos - Job {job.id}")
            job.status = StatusJobDto.EXECUTANDO
            
            # 1. Validar configuração
            await self._validar_configuracao(configuracao)
            
            # 2. Executar scraping
            cursos_coletados = await self._executar_scraping(configuracao)
            logger.info(f"Coletados {len(cursos_coletados)} cursos")
            
            # 3. Validar dados coletados
            cursos_validos = await self._validar_cursos(cursos_coletados)
            logger.info(f"Validados {len(cursos_validos)} cursos")
            
            # 4. Persistir localmente
            await self._persistir_cursos(cursos_validos)
            
            # 5. Sincronizar com backend se solicitado
            if sincronizar_backend:
                await self._sincronizar_backend(cursos_validos)
            
            # 6. Finalizar job
            job.status = StatusJobDto.CONCLUIDO
            job.concluido_em = datetime.now()
            job.itens_coletados = len(cursos_validos)
            
            logger.info(f"Scraping de cursos concluído - Job {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Erro no scraping de cursos - Job {job.id}: {e}")
            job.status = StatusJobDto.ERRO
            job.concluido_em = datetime.now()
            job.erros.append(str(e))
            job.detalhes = f"Erro durante execução: {type(e).__name__}"
            raise ScrapingException("scraping_cursos", str(e))
    
    async def obter_curso_especifico(self, codigo_curso: str) -> Optional[CursoDto]:
        """
        Obtém dados de um curso específico.
        
        Args:
            codigo_curso: Código do curso a ser coletado
            
        Returns:
            Dados do curso ou None se não encontrado
        """
        try:
            logger.info(f"Buscando curso específico: {codigo_curso}")
            
            curso = await self._scraping_service.obter_detalhes_curso(codigo_curso)
            
            if curso:
                # Validar curso
                await self._validar_curso_individual(curso)
                
                # Persistir
                await self._curso_repository.salvar(curso)
                
                return curso_para_dto(curso)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter curso {codigo_curso}: {e}")
            raise ScrapingException(f"curso_{codigo_curso}", str(e))
    
    async def listar_cursos_coletados(self, 
                                     filtro_unidade: Optional[str] = None) -> List[CursoDto]:
        """
        Lista cursos já coletados e armazenados.
        
        Args:
            filtro_unidade: Filtrar por unidade específica
            
        Returns:
            Lista de cursos coletados
        """
        try:
            if filtro_unidade:
                cursos = await self._curso_repository.listar_por_unidade(filtro_unidade)
            else:
                cursos = await self._curso_repository.listar_todos()
            
            return [curso_para_dto(curso) for curso in cursos]
            
        except Exception as e:
            logger.error(f"Erro ao listar cursos: {e}")
            raise
    
    async def _validar_configuracao(self, configuracao: ConfiguracaoScrapingDto) -> None:
        """Valida se a configuração é válida."""
        if not await self._scraping_service.validar_configuracao(configuracao.__dict__):
            raise ValidationException(
                "configuracao_scraping",
                str(configuracao),
                "Configuração inválida para scraping de cursos"
            )
    
    async def _executar_scraping(self, 
                               configuracao: ConfiguracaoScrapingDto) -> List[Curso]:
        """Executa o scraping propriamente dito."""
        return await self._scraping_service.scrape_cursos(
            filtro_unidade=configuracao.filtro_unidade,
            filtro_modalidade=configuracao.filtro_modalidade
        )
    
    async def _validar_cursos(self, cursos: List[Curso]) -> List[Curso]:
        """Valida lista de cursos coletados."""
        cursos_validos = []
        
        for curso in cursos:
            try:
                await self._validar_curso_individual(curso)
                cursos_validos.append(curso)
            except ValidationException as e:
                logger.warning(f"Curso inválido ignorado: {e}")
                continue
        
        return cursos_validos
    
    async def _validar_curso_individual(self, curso: Curso) -> None:
        """Valida um curso individual."""
        # Validações de negócio já estão na entidade
        # Aqui podemos adicionar validações específicas do caso de uso
        
        if not curso.nome.valor.strip():
            raise ValidationException(
                "nome_curso",
                str(curso.nome),
                "Nome do curso não pode estar vazio"
            )
        
        if len(curso.unidade_vinculacao.strip()) < 5:
            raise ValidationException(
                "unidade_vinculacao",
                curso.unidade_vinculacao,
                "Unidade de vinculação deve ter pelo menos 5 caracteres"
            )
    
    async def _persistir_cursos(self, cursos: List[Curso]) -> None:
        """Persiste cursos no repositório local."""
        for curso in cursos:
            try:
                await self._curso_repository.salvar(curso)
            except Exception as e:
                logger.error(f"Erro ao salvar curso {curso.codigo}: {e}")
                raise
    
    async def _sincronizar_backend(self, cursos: List[Curso]) -> None:
        """Sincroniza cursos com o backend."""
        try:
            resultado = await self._api_client.enviar_cursos(cursos)
            
            if not resultado.sucesso_total:
                logger.warning(
                    f"Sincronização parcial: {resultado.itens_com_erro} erros de "
                    f"{resultado.itens_processados} itens"
                )
            else:
                logger.info(f"Sincronização completa: {resultado.itens_processados} cursos")
                
        except Exception as e:
            logger.error(f"Erro na sincronização com backend: {e}")
            # Não falhar o job por erro de sincronização
            pass
    
    def _gerar_job_id(self) -> str:
        """Gera ID único para o job."""
        from uuid import uuid4
        return f"curso_{uuid4().hex[:8]}"