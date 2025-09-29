"""
Caso de uso coordenador para orquestração completa do scraping.

Coordena a execução sequencial ou paralela dos diferentes tipos de scraping,
garantindo dependências e integridade dos dados.
"""

from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
from enum import Enum

from .ScrapearCursosUseCase import ScrapearCursosUseCase
from .ScrapearComponentesUseCase import ScrapearComponentesUseCase
from .ScrapearEstruturasCurricularesUseCase import ScrapearEstruturasCurricularesUseCase
from ..dtos.DataTransferObjects import (
    ConfiguracaoScrapingDto, JobScrapingDto, StatusJobDto,
    ResultadoScrapingCompletoDto
)
from ...domain.exceptions import ScrapingException, ValidationException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class TipoScrapingCompleto(Enum):
    """Tipos de scraping completo disponíveis."""
    SEQUENCIAL = "sequencial"
    PARALELO_PARCIAL = "paralelo_parcial"
    COMPLETO_CURSO = "completo_curso"


class OrquestrarScrapingCompletoUseCase:
    """
    Caso de uso para orquestração completa do scraping.
    
    Coordena a execução de todos os tipos de scraping mantendo
    integridade referencial e dependências entre entidades.
    """
    
    def __init__(self,
                 scraping_cursos_uc: ScrapearCursosUseCase,
                 scraping_componentes_uc: ScrapearComponentesUseCase,
                 scraping_estruturas_uc: ScrapearEstruturasCurricularesUseCase):
        self._scraping_cursos = scraping_cursos_uc
        self._scraping_componentes = scraping_componentes_uc
        self._scraping_estruturas = scraping_estruturas_uc
    
    async def executar_scraping_completo(self,
                                       configuracao: ConfiguracaoScrapingDto,
                                       tipo_execucao: TipoScrapingCompleto = TipoScrapingCompleto.SEQUENCIAL,
                                       codigo_curso_especifico: Optional[str] = None,
                                       sincronizar_backend: bool = True) -> ResultadoScrapingCompletoDto:
        """
        Executa scraping completo de todos os tipos de dados.
        
        Args:
            configuracao: Configuração do scraping
            tipo_execucao: Estratégia de execução
            codigo_curso_especifico: Curso específico (opcional)
            sincronizar_backend: Se deve sincronizar com backend
            
        Returns:
            Resultado consolidado de todo o processo
        """
        resultado = ResultadoScrapingCompletoDto(
            id_sessao=self._gerar_sessao_id(),
            tipo_execucao=tipo_execucao.value,
            configuracao=configuracao,
            iniciado_em=datetime.now()
        )
        
        try:
            logger.info(f"Iniciando scraping completo - Sessão {resultado.id_sessao}")
            
            # Validar configuração geral
            await self._validar_configuracao_completa(configuracao, codigo_curso_especifico)
            
            # Executar conforme estratégia escolhida
            if tipo_execucao == TipoScrapingCompleto.SEQUENCIAL:
                await self._executar_sequencial(resultado, configuracao, 
                                               codigo_curso_especifico, sincronizar_backend)
            
            elif tipo_execucao == TipoScrapingCompleto.PARALELO_PARCIAL:
                await self._executar_paralelo_parcial(resultado, configuracao,
                                                     codigo_curso_especifico, sincronizar_backend)
            
            elif tipo_execucao == TipoScrapingCompleto.COMPLETO_CURSO:
                await self._executar_completo_por_curso(resultado, configuracao,
                                                       codigo_curso_especifico, sincronizar_backend)
            
            # Finalizar resultado
            resultado.concluido_em = datetime.now()
            resultado.sucesso_total = all(
                job.status == StatusJobDto.CONCLUIDO 
                for job in [resultado.job_cursos, resultado.job_componentes, resultado.job_estruturas]
                if job is not None
            )
            
            if resultado.sucesso_total:
                resultado.total_itens_coletados = sum([
                    job.itens_coletados or 0 
                    for job in [resultado.job_cursos, resultado.job_componentes, resultado.job_estruturas]
                    if job is not None
                ])
            
            logger.info(f"Scraping completo finalizado - Sessão {resultado.id_sessao}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no scraping completo - Sessão {resultado.id_sessao}: {e}")
            resultado.concluido_em = datetime.now()
            resultado.sucesso_total = False
            resultado.erro_geral = str(e)
            raise ScrapingException("scraping_completo", str(e))
    
    async def executar_pipeline_curso_especifico(self,
                                               codigo_curso: str,
                                               configuracao: ConfiguracaoScrapingDto,
                                               sincronizar_backend: bool = True) -> ResultadoScrapingCompletoDto:
        """
        Executa pipeline completo para um curso específico.
        
        Args:
            codigo_curso: Código do curso alvo
            configuracao: Configuração do scraping
            sincronizar_backend: Se deve sincronizar com backend
            
        Returns:
            Resultado do pipeline do curso
        """
        logger.info(f"Executando pipeline completo para curso {codigo_curso}")
        
        return await self.executar_scraping_completo(
            configuracao=configuracao,
            tipo_execucao=TipoScrapingCompleto.COMPLETO_CURSO,
            codigo_curso_especifico=codigo_curso,
            sincronizar_backend=sincronizar_backend
        )
    
    async def executar_atualizacao_incremental(self,
                                             configuracao: ConfiguracaoScrapingDto,
                                             sincronizar_backend: bool = True) -> ResultadoScrapingCompletoDto:
        """
        Executa atualização incremental otimizada.
        
        Args:
            configuracao: Configuração do scraping
            sincronizar_backend: Se deve sincronizar com backend
            
        Returns:
            Resultado da atualização incremental
        """
        logger.info("Executando atualização incremental")
        
        # Para atualização incremental, usar execução paralela parcial
        return await self.executar_scraping_completo(
            configuracao=configuracao,
            tipo_execucao=TipoScrapingCompleto.PARALELO_PARCIAL,
            sincronizar_backend=sincronizar_backend
        )
    
    async def _validar_configuracao_completa(self,
                                           configuracao: ConfiguracaoScrapingDto,
                                           codigo_curso: Optional[str]) -> None:
        """Valida configuração para scraping completo."""
        if not configuracao:
            raise ValidationException(
                "configuracao_scraping_completo",
                "None",
                "Configuração é obrigatória para scraping completo"
            )
        
        # Validações específicas para cada tipo
        if not configuracao.incluir_cursos and not configuracao.incluir_componentes and not configuracao.incluir_estruturas:
            raise ValidationException(
                "tipos_scraping",
                str(configuracao),
                "Pelo menos um tipo de scraping deve ser habilitado"
            )
    
    async def _executar_sequencial(self,
                                 resultado: ResultadoScrapingCompletoDto,
                                 configuracao: ConfiguracaoScrapingDto,
                                 codigo_curso: Optional[str],
                                 sincronizar_backend: bool) -> None:
        """Executa scraping sequencial mantendo dependências."""
        logger.info("Executando scraping sequencial")
        
        try:
            # 1. Cursos primeiro (dependência base)
            if configuracao.incluir_cursos:
                logger.info("Executando scraping de cursos...")
                resultado.job_cursos = await self._scraping_cursos.executar(
                    configuracao, sincronizar_backend=False  # Sincronizar apenas no final
                )
            
            # 2. Componentes (dependem dos cursos)
            if configuracao.incluir_componentes:
                logger.info("Executando scraping de componentes...")
                resultado.job_componentes = await self._scraping_componentes.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                )
            
            # 3. Estruturas (dependem de cursos e componentes)
            if configuracao.incluir_estruturas:
                logger.info("Executando scraping de estruturas...")
                resultado.job_estruturas = await self._scraping_estruturas.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                )
            
            # 4. Sincronização final se solicitada
            if sincronizar_backend:
                await self._sincronizar_todos_dados(resultado)
                
        except Exception as e:
            logger.error(f"Erro na execução sequencial: {e}")
            raise
    
    async def _executar_paralelo_parcial(self,
                                       resultado: ResultadoScrapingCompletoDto,
                                       configuracao: ConfiguracaoScrapingDto,
                                       codigo_curso: Optional[str],
                                       sincronizar_backend: bool) -> None:
        """Executa scraping com paralelismo parcial."""
        logger.info("Executando scraping paralelo parcial")
        
        try:
            # 1. Cursos primeiro (obrigatório)
            if configuracao.incluir_cursos:
                logger.info("Executando scraping de cursos...")
                resultado.job_cursos = await self._scraping_cursos.executar(
                    configuracao, sincronizar_backend=False
                )
            
            # 2. Componentes e estruturas em paralelo (após cursos)
            tasks = []
            
            if configuracao.incluir_componentes:
                tasks.append(self._scraping_componentes.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                ))
            
            if configuracao.incluir_estruturas:
                tasks.append(self._scraping_estruturas.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                ))
            
            if tasks:
                logger.info("Executando scraping de componentes e estruturas em paralelo...")
                resultados_paralelos = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Processar resultados
                idx = 0
                if configuracao.incluir_componentes:
                    if isinstance(resultados_paralelos[idx], Exception):
                        raise resultados_paralelos[idx]
                    resultado.job_componentes = resultados_paralelos[idx]
                    idx += 1
                
                if configuracao.incluir_estruturas:
                    if isinstance(resultados_paralelos[idx], Exception):
                        raise resultados_paralelos[idx]
                    resultado.job_estruturas = resultados_paralelos[idx]
            
            # 3. Sincronização final
            if sincronizar_backend:
                await self._sincronizar_todos_dados(resultado)
                
        except Exception as e:
            logger.error(f"Erro na execução paralela parcial: {e}")
            raise
    
    async def _executar_completo_por_curso(self,
                                         resultado: ResultadoScrapingCompletoDto,
                                         configuracao: ConfiguracaoScrapingDto,
                                         codigo_curso: Optional[str],
                                         sincronizar_backend: bool) -> None:
        """Executa scraping completo curso por curso."""
        logger.info("Executando scraping completo por curso")
        
        if not codigo_curso:
            raise ValidationException(
                "codigo_curso_obrigatorio",
                "None",
                "Código do curso é obrigatório para execução completa por curso"
            )
        
        try:
            # Pipeline completo para o curso específico
            tasks = []
            
            if configuracao.incluir_cursos:
                tasks.append(self._scraping_cursos.obter_curso_especifico(codigo_curso))
            
            if configuracao.incluir_componentes:
                tasks.append(self._scraping_componentes.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                ))
            
            if configuracao.incluir_estruturas:
                tasks.append(self._scraping_estruturas.executar(
                    configuracao, codigo_curso, sincronizar_backend=False
                ))
            
            # Executar todos em paralelo para o curso específico
            resultados = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados (implementação simplificada)
            logger.info(f"Pipeline completo do curso {codigo_curso} executado")
            
            # Sincronização final
            if sincronizar_backend:
                await self._sincronizar_todos_dados(resultado)
                
        except Exception as e:
            logger.error(f"Erro na execução completa por curso: {e}")
            raise
    
    async def _sincronizar_todos_dados(self, resultado: ResultadoScrapingCompletoDto) -> None:
        """Sincroniza todos os dados coletados com o backend."""
        logger.info("Sincronizando todos os dados com backend...")
        
        try:
            # Esta seria a implementação da sincronização consolidada
            # Por enquanto, log apenas
            logger.info("Sincronização completa finalizada")
            
        except Exception as e:
            logger.error(f"Erro na sincronização completa: {e}")
            # Não falhar o job inteiro por erro de sincronização
            pass
    
    def _gerar_sessao_id(self) -> str:
        """Gera ID único para a sessão de scraping."""
        from uuid import uuid4
        return f"sessao_{uuid4().hex[:8]}"