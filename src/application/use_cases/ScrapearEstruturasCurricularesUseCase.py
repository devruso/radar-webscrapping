"""
Caso de uso para scraping de estruturas curriculares.

Implementa a lógica de negócio para coleta de estruturas curriculares
completas, incluindo relações entre cursos e componentes.
"""

from typing import List, Optional, Dict, Set
import asyncio
from datetime import datetime

from ..interfaces.ICursoRepository import ICursoRepository
from ..interfaces.IComponenteCurricularRepository import IComponenteCurricularRepository
from ..interfaces.IEstruturaCurricularRepository import IEstruturaCurricularRepository
from ..interfaces.IScrapingService import IEstruturaCurricularScrapingService
from ..interfaces.IRadarApiClient import IRadarApiClient
from ..dtos.DataTransferObjects import (
    EstruturaCurricularDto, ConfiguracaoScrapingDto, JobScrapingDto,
    StatusJobDto, estrutura_curricular_para_dto, CursoDto
)
from ...domain.entities import EstruturaCurricular, Curso, ComponenteCurricular
from ...domain.exceptions import ScrapingException, ValidationException, BusinessRuleException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class ScrapearEstruturasCurricularesUseCase:
    """
    Caso de uso para scraping de estruturas curriculares.
    
    Coordena o processo completo de coleta de estruturas curriculares,
    incluindo validação de integridade e consistência dos dados.
    """
    
    def __init__(self,
                 estrutura_repository: IEstruturaCurricularRepository,
                 curso_repository: ICursoRepository,
                 componente_repository: IComponenteCurricularRepository,
                 scraping_service: IEstruturaCurricularScrapingService,
                 api_client: IRadarApiClient):
        self._estrutura_repository = estrutura_repository
        self._curso_repository = curso_repository
        self._componente_repository = componente_repository
        self._scraping_service = scraping_service
        self._api_client = api_client
    
    async def executar(self,
                      configuracao: ConfiguracaoScrapingDto,
                      codigo_curso: Optional[str] = None,
                      sincronizar_backend: bool = True) -> JobScrapingDto:
        """
        Executa o scraping de estruturas curriculares.
        
        Args:
            configuracao: Parâmetros de configuração do scraping
            codigo_curso: Código específico do curso (opcional)
            sincronizar_backend: Se deve sincronizar com o backend
            
        Returns:
            Resultado do job de scraping
        """
        job = JobScrapingDto(
            id=self._gerar_job_id(),
            tipo_scraping="estruturas",
            status=StatusJobDto.PENDENTE,
            configuracao=configuracao,
            iniciado_em=datetime.now()
        )
        
        try:
            logger.info(f"Iniciando scraping de estruturas curriculares - Job {job.id}")
            job.status = StatusJobDto.EXECUTANDO
            
            # 1. Validar configuração
            await self._validar_configuracao(configuracao, codigo_curso)
            
            # 2. Obter cursos relacionados
            cursos_alvo = await self._obter_cursos_alvo(codigo_curso)
            logger.info(f"Processando estruturas de {len(cursos_alvo)} cursos")
            
            # 3. Executar scraping para cada curso
            estruturas_coletadas = []
            for curso in cursos_alvo:
                estruturas_curso = await self._scrape_estruturas_por_curso(curso, configuracao)
                estruturas_coletadas.extend(estruturas_curso)
            
            logger.info(f"Coletadas {len(estruturas_coletadas)} estruturas")
            
            # 4. Validar dados coletados
            estruturas_validas = await self._validar_estruturas(estruturas_coletadas)
            logger.info(f"Validadas {len(estruturas_validas)} estruturas")
            
            # 5. Validar integridade referencial
            await self._validar_integridade_referencial(estruturas_validas)
            
            # 6. Persistir localmente
            await self._persistir_estruturas(estruturas_validas)
            
            # 7. Sincronizar com backend se solicitado
            if sincronizar_backend:
                await self._sincronizar_backend(estruturas_validas)
            
            # 8. Finalizar job
            job.status = StatusJobDto.CONCLUIDO
            job.concluido_em = datetime.now()
            job.itens_coletados = len(estruturas_validas)
            
            logger.info(f"Scraping de estruturas curriculares concluído - Job {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Erro no scraping de estruturas - Job {job.id}: {e}")
            job.status = StatusJobDto.ERRO
            job.concluido_em = datetime.now()
            job.erros.append(str(e))
            job.detalhes = f"Erro durante execução: {type(e).__name__}"
            raise ScrapingException("scraping_estruturas", str(e))
    
    async def obter_estrutura_especifica(self, 
                                       codigo_curso: str,
                                       versao_estrutura: str) -> Optional[EstruturaCurricularDto]:
        """
        Obtém dados de uma estrutura curricular específica.
        
        Args:
            codigo_curso: Código do curso relacionado
            versao_estrutura: Versão/período da estrutura
            
        Returns:
            Dados da estrutura ou None se não encontrada
        """
        try:
            logger.info(f"Buscando estrutura específica: {codigo_curso} v{versao_estrutura}")
            
            # Verificar se curso existe
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            if not curso:
                raise ValidationException(
                    "curso_inexistente", 
                    codigo_curso,
                    f"Curso {codigo_curso} não encontrado"
                )
            
            estrutura = await self._scraping_service.obter_estrutura_curso(
                codigo_curso, versao_estrutura
            )
            
            if estrutura:
                # Validar estrutura
                await self._validar_estrutura_individual(estrutura)
                
                # Validar integridade referencial
                await self._validar_integridade_estrutura_individual(estrutura)
                
                # Persistir
                await self._estrutura_repository.salvar(estrutura)
                
                return estrutura_curricular_para_dto(estrutura)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter estrutura {codigo_curso} v{versao_estrutura}: {e}")
            raise ScrapingException(f"estrutura_{codigo_curso}_{versao_estrutura}", str(e))
    
    async def listar_estruturas_por_curso(self, 
                                        codigo_curso: str) -> List[EstruturaCurricularDto]:
        """
        Lista estruturas curriculares de um curso específico.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Lista de estruturas do curso
        """
        try:
            estruturas = await self._estrutura_repository.listar_por_curso(codigo_curso)
            return [estrutura_curricular_para_dto(est) for est in estruturas]
            
        except Exception as e:
            logger.error(f"Erro ao listar estruturas do curso {codigo_curso}: {e}")
            raise
    
    async def obter_estrutura_ativa(self, codigo_curso: str) -> Optional[EstruturaCurricularDto]:
        """
        Obtém a estrutura curricular ativa de um curso.
        
        Args:
            codigo_curso: Código do curso
            
        Returns:
            Estrutura ativa ou None se não encontrada
        """
        try:
            estrutura = await self._estrutura_repository.buscar_ativa_por_curso(codigo_curso)
            return estrutura_curricular_para_dto(estrutura) if estrutura else None
            
        except Exception as e:
            logger.error(f"Erro ao obter estrutura ativa do curso {codigo_curso}: {e}")
            raise
    
    async def _validar_configuracao(self, 
                                  configuracao: ConfiguracaoScrapingDto,
                                  codigo_curso: Optional[str]) -> None:
        """Valida se a configuração é válida."""
        if not await self._scraping_service.validar_configuracao(configuracao.__dict__):
            raise ValidationException(
                "configuracao_scraping",
                str(configuracao),
                "Configuração inválida para scraping de estruturas"
            )
        
        # Validar se curso específico existe
        if codigo_curso:
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            if not curso:
                raise ValidationException(
                    "curso_inexistente",
                    codigo_curso,
                    f"Curso {codigo_curso} não encontrado para scraping de estruturas"
                )
    
    async def _obter_cursos_alvo(self, codigo_curso: Optional[str]) -> List[Curso]:
        """Obtém lista de cursos para processar."""
        if codigo_curso:
            curso = await self._curso_repository.buscar_por_codigo(codigo_curso)
            return [curso] if curso else []
        else:
            return await self._curso_repository.listar_todos()
    
    async def _scrape_estruturas_por_curso(self, 
                                         curso: Curso,
                                         configuracao: ConfiguracaoScrapingDto) -> List[EstruturaCurricular]:
        """Executa scraping de estruturas para um curso específico."""
        try:
            logger.info(f"Coletando estruturas do curso {curso.codigo}")
            
            estruturas = await self._scraping_service.scrape_estruturas_curso(
                codigo_curso=curso.codigo.valor,
                incluir_historicas=configuracao.incluir_estruturas_historicas,
                incluir_pre_requisitos=configuracao.incluir_pre_requisitos
            )
            
            logger.info(f"Coletadas {len(estruturas)} estruturas do curso {curso.codigo}")
            return estruturas
            
        except Exception as e:
            logger.error(f"Erro ao coletar estruturas do curso {curso.codigo}: {e}")
            # Não falhar todo o job por erro em um curso
            return []
    
    async def _validar_estruturas(self, 
                                estruturas: List[EstruturaCurricular]) -> List[EstruturaCurricular]:
        """Valida lista de estruturas coletadas."""
        estruturas_validas = []
        
        for estrutura in estruturas:
            try:
                await self._validar_estrutura_individual(estrutura)
                estruturas_validas.append(estrutura)
            except ValidationException as e:
                logger.warning(f"Estrutura inválida ignorada: {e}")
                continue
        
        return estruturas_validas
    
    async def _validar_estrutura_individual(self, estrutura: EstruturaCurricular) -> None:
        """Valida uma estrutura curricular individual."""
        # Validações de negócio já estão na entidade
        # Aqui podemos adicionar validações específicas do caso de uso
        
        if not estrutura.codigo_curso:
            raise ValidationException(
                "codigo_curso_estrutura",
                str(estrutura.versao),
                "Código do curso não pode estar vazio na estrutura"
            )
        
        if len(estrutura.componentes) == 0:
            raise ValidationException(
                "componentes_estrutura",
                str(estrutura.versao),
                "Estrutura curricular deve ter pelo menos um componente"
            )
        
        # Validar carga horária total
        carga_total = estrutura.calcular_carga_horaria_total()
        if carga_total.valor < 1600:  # Mínimo para graduação
            logger.warning(f"Estrutura {estrutura.versao} com carga horária baixa: {carga_total}")
    
    async def _validar_integridade_referencial(self, 
                                             estruturas: List[EstruturaCurricular]) -> None:
        """Valida integridade referencial das estruturas."""
        for estrutura in estruturas:
            await self._validar_integridade_estrutura_individual(estrutura)
    
    async def _validar_integridade_estrutura_individual(self, 
                                                      estrutura: EstruturaCurricular) -> None:
        """Valida integridade de uma estrutura individual."""
        # 1. Validar se curso existe
        curso = await self._curso_repository.buscar_por_codigo(estrutura.codigo_curso)
        if not curso:
            raise BusinessRuleException(
                f"Curso {estrutura.codigo_curso} da estrutura {estrutura.versao} não encontrado"
            )
        
        # 2. Validar se componentes existem
        componentes_inexistentes = []
        for codigo_componente in estrutura.componentes:
            componente = await self._componente_repository.buscar_por_codigo(
                codigo_componente, estrutura.codigo_curso
            )
            if not componente:
                componentes_inexistentes.append(codigo_componente)
        
        if componentes_inexistentes:
            logger.warning(
                f"Estrutura {estrutura.versao}: componentes não encontrados: "
                f"{componentes_inexistentes}"
            )
        
        # 3. Validar pré-requisitos
        await self._validar_pre_requisitos_estrutura(estrutura)
    
    async def _validar_pre_requisitos_estrutura(self, estrutura: EstruturaCurricular) -> None:
        """Valida pré-requisitos da estrutura curricular."""
        componentes_estrutura = set(estrutura.componentes)
        
        for codigo_componente in estrutura.componentes:
            componente = await self._componente_repository.buscar_por_codigo(
                codigo_componente, estrutura.codigo_curso
            )
            
            if componente and componente.pre_requisitos:
                for pre_req in componente.pre_requisitos:
                    if pre_req not in componentes_estrutura:
                        logger.warning(
                            f"Pré-requisito {pre_req} do componente {codigo_componente} "
                            f"não está na estrutura {estrutura.versao}"
                        )
    
    async def _persistir_estruturas(self, estruturas: List[EstruturaCurricular]) -> None:
        """Persiste estruturas no repositório local."""
        for estrutura in estruturas:
            try:
                await self._estrutura_repository.salvar(estrutura)
            except Exception as e:
                logger.error(f"Erro ao salvar estrutura {estrutura.versao}: {e}")
                raise
    
    async def _sincronizar_backend(self, estruturas: List[EstruturaCurricular]) -> None:
        """Sincroniza estruturas com o backend."""
        try:
            resultado = await self._api_client.enviar_estruturas(estruturas)
            
            if not resultado.sucesso_total:
                logger.warning(
                    f"Sincronização parcial: {resultado.itens_com_erro} erros de "
                    f"{resultado.itens_processados} itens"
                )
            else:
                logger.info(f"Sincronização completa: {resultado.itens_processados} estruturas")
                
        except Exception as e:
            logger.error(f"Erro na sincronização com backend: {e}")
            # Não falhar o job por erro de sincronização
            pass
    
    def _gerar_job_id(self) -> str:
        """Gera ID único para o job."""
        from uuid import uuid4
        return f"estrutura_{uuid4().hex[:8]}"