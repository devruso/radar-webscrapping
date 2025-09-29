"""
Cliente HTTP para comunicação com o radar-webapi.

Implementa a interface IRadarApiClient para comunicação
com o backend Spring Boot da aplicação Radar.
"""

from typing import List, Optional, Dict, Any
import asyncio
import httpx
from datetime import datetime

from ...application.interfaces.IRadarApiClient import IRadarApiClient
from ...application.dtos.DataTransferObjects import (
    ResultadoSincronizacaoDto, HealthCheckDto
)
from ...domain.entities import Curso, ComponenteCurricular, EstruturaCurricular
from ...domain.exceptions import ApiException, ValidationException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class RadarApiClient(IRadarApiClient):
    """
    Cliente concreto para comunicação com radar-webapi.
    
    Implementa comunicação HTTP assíncrona com o backend
    Spring Boot usando httpx.
    """
    
    def __init__(self,
                 base_url: str = "http://localhost:8080/api",
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Inicializa o cliente da API.
        
        Args:
            base_url: URL base da API
            timeout: Timeout das requisições em segundos
            max_retries: Número máximo de tentativas
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém cliente HTTP configurado."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "radar-webscrapping/1.0.0"
                }
            )
        return self._client
    
    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def verificar_saude(self) -> HealthCheckDto:
        """
        Verifica saúde da API.
        
        Returns:
            Status de saúde da API
        """
        try:
            client = await self._get_client()
            
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            data = response.json()
            
            return HealthCheckDto(
                status=data.get("status", "unknown"),
                timestamp=datetime.now(),
                versao=data.get("version", "unknown"),
                detalhes=data.get("details", {})
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP no health check: {e}")
            return HealthCheckDto(
                status="error",
                timestamp=datetime.now(),
                versao="unknown",
                detalhes={"erro": str(e)}
            )
        
        except Exception as e:
            logger.error(f"Erro no health check: {e}")
            return HealthCheckDto(
                status="error",
                timestamp=datetime.now(),
                versao="unknown",
                detalhes={"erro": str(e)}
            )
    
    async def enviar_cursos(self, cursos: List[Curso]) -> ResultadoSincronizacaoDto:
        """
        Envia lista de cursos para o backend.
        
        Args:
            cursos: Lista de cursos a serem enviados
            
        Returns:
            Resultado da sincronização
        """
        try:
            logger.info(f"Enviando {len(cursos)} cursos para API")
            
            client = await self._get_client()
            
            # Converter cursos para payload
            payload = {
                "cursos": [self._curso_para_dict(curso) for curso in cursos],
                "timestamp": datetime.now().isoformat(),
                "fonte": "sigaa-ufba"
            }
            
            response = await client.post(
                f"{self.base_url}/cursos/bulk",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            resultado = ResultadoSincronizacaoDto(
                sucesso_total=data.get("sucesso_total", False),
                itens_processados=data.get("itens_processados", 0),
                itens_com_erro=data.get("itens_com_erro", 0),
                timestamp=datetime.now(),
                detalhes=data.get("detalhes", {})
            )
            
            logger.info(f"Cursos enviados - {resultado.itens_processados} processados")
            return resultado
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar cursos: {e}")
            raise ApiException(f"Erro na comunicação: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao enviar cursos: {e}")
            raise ApiException(f"Erro inesperado: {e}")
    
    async def enviar_componentes(self, 
                               componentes: List[ComponenteCurricular]) -> ResultadoSincronizacaoDto:
        """
        Envia lista de componentes curriculares para o backend.
        
        Args:
            componentes: Lista de componentes a serem enviados
            
        Returns:
            Resultado da sincronização
        """
        try:
            logger.info(f"Enviando {len(componentes)} componentes para API")
            
            client = await self._get_client()
            
            # Converter componentes para payload
            payload = {
                "componentes": [self._componente_para_dict(comp) for comp in componentes],
                "timestamp": datetime.now().isoformat(),
                "fonte": "sigaa-ufba"
            }
            
            response = await client.post(
                f"{self.base_url}/componentes/bulk",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            resultado = ResultadoSincronizacaoDto(
                sucesso_total=data.get("sucesso_total", False),
                itens_processados=data.get("itens_processados", 0),
                itens_com_erro=data.get("itens_com_erro", 0),
                timestamp=datetime.now(),
                detalhes=data.get("detalhes", {})
            )
            
            logger.info(f"Componentes enviados - {resultado.itens_processados} processados")
            return resultado
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar componentes: {e}")
            raise ApiException(f"Erro na comunicação: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao enviar componentes: {e}")
            raise ApiException(f"Erro inesperado: {e}")
    
    async def enviar_estruturas(self, 
                              estruturas: List[EstruturaCurricular]) -> ResultadoSincronizacaoDto:
        """
        Envia lista de estruturas curriculares para o backend.
        
        Args:
            estruturas: Lista de estruturas a serem enviadas
            
        Returns:
            Resultado da sincronização
        """
        try:
            logger.info(f"Enviando {len(estruturas)} estruturas para API")
            
            client = await self._get_client()
            
            # Converter estruturas para payload
            payload = {
                "estruturas": [self._estrutura_para_dict(est) for est in estruturas],
                "timestamp": datetime.now().isoformat(),
                "fonte": "sigaa-ufba"
            }
            
            response = await client.post(
                f"{self.base_url}/estruturas/bulk",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            resultado = ResultadoSincronizacaoDto(
                sucesso_total=data.get("sucesso_total", False),
                itens_processados=data.get("itens_processados", 0),
                itens_com_erro=data.get("itens_com_erro", 0),
                timestamp=datetime.now(),
                detalhes=data.get("detalhes", {})
            )
            
            logger.info(f"Estruturas enviadas - {resultado.itens_processados} processados")
            return resultado
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar estruturas: {e}")
            raise ApiException(f"Erro na comunicação: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao enviar estruturas: {e}")
            raise ApiException(f"Erro inesperado: {e}")
    
    async def obter_configuracao_sistema(self) -> Dict[str, Any]:
        """
        Obtém configuração do sistema backend.
        
        Returns:
            Configuração do sistema
        """
        try:
            client = await self._get_client()
            
            response = await client.get(f"{self.base_url}/config")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro ao obter configuração: {e}")
            raise ApiException(f"Erro na comunicação: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao obter configuração: {e}")
            raise ApiException(f"Erro inesperado: {e}")
    
    def _curso_para_dict(self, curso: Curso) -> Dict[str, Any]:
        """Converte entidade Curso para dicionário."""
        return {
            "codigo": str(curso.codigo),
            "nome": str(curso.nome),
            "unidadeVinculacao": curso.unidade_vinculacao,
            "municipioFuncionamento": curso.municipio_funcionamento,
            "modalidade": curso.modalidade,
            "turno": curso.turno,
            "grauAcademico": curso.grau_academico,
            "urlOrigem": curso.url_origem
        }
    
    def _componente_para_dict(self, componente: ComponenteCurricular) -> Dict[str, Any]:
        """Converte entidade ComponenteCurricular para dicionário."""
        return {
            "codigo": str(componente.codigo),
            "nome": componente.nome,
            "tipo": componente.tipo.value,
            "modalidade": componente.modalidade.value,
            "cargaHoraria": {
                "teorica": componente.carga_horaria.teorica,
                "pratica": componente.carga_horaria.pratica,
                "estagio": componente.carga_horaria.estagio,
                "total": componente.carga_horaria.total
            },
            "unidadeResponsavel": componente.unidade_responsavel,
            "departamento": componente.departamento,
            "preRequisitos": list(componente.pre_requisitos) if componente.pre_requisitos else [],
            "coRequisitos": list(componente.co_requisitos) if componente.co_requisitos else [],
            "equivalencias": list(componente.equivalencias) if componente.equivalencias else [],
            "ementaDescricao": componente.ementa_descricao,
            "matriculavelOnline": componente.matriculavel_online,
            "urlOrigem": componente.url_origem,
            "codigoCurso": componente.codigo_curso
        }
    
    def _estrutura_para_dict(self, estrutura: EstruturaCurricular) -> Dict[str, Any]:
        """Converte entidade EstruturaCurricular para dicionário."""
        return {
            "codigo": estrutura.codigo,
            "codigoCurso": estrutura.codigo_curso,
            "matrizCurricular": estrutura.matriz_curricular,
            "anoPeriodoVigencia": str(estrutura.ano_periodo_vigencia),
            "situacao": estrutura.situacao.value,
            "unidadeVinculacao": estrutura.unidade_vinculacao,
            "municipioFuncionamento": estrutura.municipio_funcionamento,
            "prazos": {
                "minimo": estrutura.prazos_conclusao.minimo,
                "medio": estrutura.prazos_conclusao.medio,
                "maximo": estrutura.prazos_conclusao.maximo
            },
            "cargaHoraria": {
                "obrigatoria": estrutura.carga_horaria_obrigatoria,
                "optativa": estrutura.carga_horaria_optativa,
                "complementar": estrutura.carga_horaria_complementar,
                "optativaLivre": estrutura.carga_horaria_optativa_livre
            },
            "componentesPorPeriodo": {
                str(periodo): [
                    {
                        "codigoComponente": comp.codigo_componente,
                        "periodoSugerido": comp.periodo_sugerido,
                        "natureza": comp.natureza.value,
                        "cargaHoraria": comp.carga_horaria.total
                    } for comp in componentes
                ] for periodo, componentes in estrutura.componentes_por_periodo.items()
            },
            "urlOrigem": estrutura.url_origem
        }