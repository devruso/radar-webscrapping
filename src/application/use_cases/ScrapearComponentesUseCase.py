"""
Caso de uso para scraping de componentes curriculares.

Implementa a lógica de negócio para coleta de dados de componentes
curriculares do SIGAA, incluindo relação com cursos.
"""

from typing import List, Optional, Dict
import asyncio
from datetime import datetime

from ..interfaces.ICursoRepository import ICursoRepository
from ..interfaces.IComponenteCurricularRepository import IComponenteCurricularRepository
from ..interfaces.IScrapingService import IComponenteCurricularScrapingService
from ..interfaces.IRadarApiClient import IRadarApiClient
from ..dtos.DataTransferObjects import (
    ComponenteCurricularDto, ConfiguracaoScrapingDto, JobScrapingDto,
    StatusJobDto, componente_curricular_para_dto
)
from ...domain.entities import ComponenteCurricular, Curso
from ...domain.exceptions import ScrapingException, ValidationException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class ScrapearComponentesUseCase:
    """
    Caso de uso para scraping de componentes curriculares.
    
    Coordena o processo completo de coleta de componentes curriculares,
    incluindo validação de dependências com cursos.
    """
    
    def __init__(self,
                 componente_repository: IComponenteCurricularRepository,
                 curso_repository: ICursoRepository,
                 scraping_service: IComponenteCurricularScrapingService,
                 api_client: IRadarApiClient):
        self._componente_repository = componente_repository
        self._curso_repository = curso_repository
        self._scraping_service = scraping_service
        self._api_client = api_client
    
    async def executar(self,
                      configuracao: ConfiguracaoScrapingDto,
                      codigo_curso: Optional[str] = None,
                      sincronizar_backend: bool = True) -> JobScrapingDto:
        """
        Executa o scraping de componentes curriculares.
        
        Args:
            configuracao: Parâmetros de configuração do scraping
            codigo_curso: Código específico do curso (opcional)
            sincronizar_backend: Se deve sincronizar com o backend
            
        Returns:
            Resultado do job de scraping
        """
        job = JobScrapingDto(
            id=self._gerar_job_id(),
            tipo_scraping="componentes",
            status=StatusJobDto.PENDENTE,
            configuracao=configuracao,
            iniciado_em=datetime.now()
        )
        
        try:
            logger.info(f"Iniciando scraping de componentes - Job {job.id}")
            job.status = StatusJobDto.EXECUTANDO
            
            # 1. Validar configuração
            await self._validar_configuracao(configuracao, codigo_curso)
            
            # 2. Obter cursos relacionados
            cursos_alvo = await self._obter_cursos_alvo(codigo_curso)
            logger.info(f"Processando componentes de {len(cursos_alvo)} cursos")
            
            # 3. Executar scraping para cada curso
            componentes_coletados = []
            for curso in cursos_alvo:
                componentes_curso = await self._scrape_componentes_por_curso(curso, configuracao)
                componentes_coletados.extend(componentes_curso)
            
            logger.info(f"Coletados {len(componentes_coletados)} componentes")
            
            # 4. Validar dados coletados
            componentes_validos = await self._validar_componentes(componentes_coletados)
            logger.info(f"Validados {len(componentes_validos)} componentes")
            
            # 5. Persistir localmente
            await self._persistir_componentes(componentes_validos)
            
            # 6. Sincronizar com backend se solicitado
            if sincronizar_backend:
                await self._sincronizar_backend(componentes_validos)
            
            # 7. Finalizar job
            job.status = StatusJobDto.CONCLUIDO
            job.concluido_em = datetime.now()
            job.itens_coletados = len(componentes_validos)
            
            logger.info(f"Scraping de componentes concluído - Job {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Erro no scraping de componentes - Job {job.id}: {e}")
            job.status = StatusJobDto.ERRO
            job.concluido_em = datetime.now()
            job.erros.append(str(e))
            job.detalhes = f"Erro durante execução: {type(e).__name__}"
            raise ScrapingException("scraping_componentes", str(e))
    
    async def obter_componente_especifico(self, 
                                        codigo_componente: str,
                                        codigo_curso: str) -> Optional[ComponenteCurricularDto]:
        """
        Obtém dados de um componente curricular específico.
        
        Args:
            codigo_componente: Código do componente a ser coletado
            codigo_curso: Código do curso relacionado
            
        Returns:
            Dados do componente ou None se não encontrado
        """
        try:
            logger.info(f"Buscando componente específico: {codigo_componente} do curso {codigo_curso}")
            
            # Verificar se curso existe
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            if not curso:
                raise ValidationException(
                    "curso_inexistente",
                    codigo_curso,
                    f"Curso {codigo_curso} não encontrado"
                )
            
            componente = await self._scraping_service.obter_detalhes_componente(
                codigo_componente, codigo_curso
            )
            
            if componente:
                # Validar componente
                await self._validar_componente_individual(componente)
                
                # Persistir
                await self._componente_repository.salvar(componente)
                
                return componente_curricular_para_dto(componente)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter componente {codigo_componente}: {e}")
            raise ScrapingException(f"componente_{codigo_componente}", str(e))
    
    async def listar_componentes_por_curso(self, 
                                          codigo_curso: str) -> List[ComponenteCurricularDto]:
        """
        Lista componentes curriculares de um curso específico.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Lista de componentes do curso
        """
        try:
            componentes = await self._componente_repository.listar_por_curso(codigo_curso)
            return [componente_curricular_para_dto(comp) for comp in componentes]
            
        except Exception as e:
            logger.error(f"Erro ao listar componentes do curso {codigo_curso}: {e}")
            raise
    
    async def listar_componentes_por_departamento(self, 
                                                 departamento: str) -> List[ComponenteCurricularDto]:
        """
        Lista componentes curriculares por departamento.
        
        Args:
            departamento: Nome ou código do departamento
            
        Returns:
            Lista de componentes do departamento
        """
        try:
            componentes = await self._componente_repository.listar_por_departamento(departamento)
            return [componente_curricular_para_dto(comp) for comp in componentes]
            
        except Exception as e:
            logger.error(f"Erro ao listar componentes do departamento {departamento}: {e}")
            raise
    
    async def _validar_configuracao(self, 
                                  configuracao: ConfiguracaoScrapingDto,
                                  codigo_curso: Optional[str]) -> None:
        """Valida se a configuração é válida."""
        if not await self._scraping_service.validar_configuracao(configuracao.__dict__):
            raise ValidationException(
                "configuracao_scraping",
                str(configuracao),
                "Configuração inválida para scraping de componentes"
            )
        
        # Validar se curso específico existe
        if codigo_curso:
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            if not curso:
                raise ValidationException(
                    "curso_inexistente",
                    codigo_curso,
                    f"Curso {codigo_curso} não encontrado para scraping de componentes"
                )
    
    async def _obter_cursos_alvo(self, codigo_curso: Optional[str]) -> List[Curso]:
        """Obtém lista de cursos para processar."""
        if codigo_curso:
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            return [curso] if curso else []
        else:
            return await self._curso_repository.listar_todos()
    
    async def _scrape_componentes_por_curso(self, 
                                          curso: Curso,
                                          configuracao: ConfiguracaoScrapingDto) -> List[ComponenteCurricular]:
        """Executa scraping de componentes para um curso específico."""
        try:
            logger.info(f"Coletando componentes do curso {curso.codigo}")
            
            componentes = await self._scraping_service.scrape_componentes_curso(
                codigo_curso=curso.codigo.valor,
                incluir_pre_requisitos=configuracao.incluir_pre_requisitos,
                incluir_equivalencias=configuracao.incluir_equivalencias
            )
            
            logger.info(f"Coletados {len(componentes)} componentes do curso {curso.codigo}")
            return componentes
            
        except Exception as e:
            logger.error(f"Erro ao coletar componentes do curso {curso.codigo}: {e}")
            # Não falhar todo o job por erro em um curso
            return []
    
    async def _validar_componentes(self, 
                                 componentes: List[ComponenteCurricular]) -> List[ComponenteCurricular]:
        """Valida lista de componentes coletados."""
        componentes_validos = []
        
        for componente in componentes:
            try:
                await self._validar_componente_individual(componente)
                componentes_validos.append(componente)
            except ValidationException as e:
                logger.warning(f"Componente inválido ignorado: {e}")
                continue
        
        return componentes_validos
    
    async def _validar_componente_individual(self, componente: ComponenteCurricular) -> None:
        """Valida um componente curricular individual."""
        # Validações de negócio já estão na entidade
        # Aqui podemos adicionar validações específicas do caso de uso
        
        if not componente.nome.strip():
            raise ValidationException(
                "nome_componente",
                str(componente.codigo),
                "Nome do componente não pode estar vazio"
            )
        
        if not componente.departamento.strip():
            raise ValidationException(
                "departamento_componente",
                str(componente.codigo),
                "Departamento do componente não pode estar vazio"
            )
        
        # Validar se curso relacionado existe
        curso = await self._curso_repository.buscar_por_codigo(componente.codigo_curso)
        if not curso:
            raise ValidationException(
                "curso_componente_inexistente",
                componente.codigo_curso,
                f"Curso {componente.codigo_curso} do componente {componente.codigo} não encontrado"
            )
    
    async def _persistir_componentes(self, componentes: List[ComponenteCurricular]) -> None:
        """Persiste componentes no repositório local."""
        for componente in componentes:
            try:
                await self._componente_repository.salvar(componente)
            except Exception as e:
                logger.error(f"Erro ao salvar componente {componente.codigo}: {e}")
                raise
    
    async def _sincronizar_backend(self, componentes: List[ComponenteCurricular]) -> None:
        """Sincroniza componentes com o backend."""
        try:
            resultado = await self._api_client.enviar_componentes(componentes)
            
            if not resultado.sucesso_total:
                logger.warning(
                    f"Sincronização parcial: {resultado.itens_com_erro} erros de "
                    f"{resultado.itens_processados} itens"
                )
            else:
                logger.info(f"Sincronização completa: {resultado.itens_processados} componentes")
                
        except Exception as e:
            logger.error(f"Erro na sincronização com backend: {e}")
            # Não falhar o job por erro de sincronização
            pass
    
    def _gerar_job_id(self) -> str:
        """Gera ID único para o job."""
        from uuid import uuid4
        return f"componente_{uuid4().hex[:8]}"