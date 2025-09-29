"""
Cliente HTTP para comunicação com a API backend (radar-webapi).

Este módulo fornece interface simplificada para:
1. Envio de dados coletados para o backend
2. Sincronização de informações entre sistemas
3. Monitoramento de status da API
4. Retry automático e tratamento de erros
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.scraped_data import Course, Schedule, Professor, SyllabusData, BaseScrapedData
from ..config.settings import config


class APIClient:
    """
    Cliente HTTP para comunicação com o backend radar-webapi.
    
    Fornece métodos para enviar dados coletados pelo web scraping
    para a API backend, com retry automático e tratamento de erros.
    """
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Inicializa o cliente da API.
        
        Args:
            base_url: URL base da API (usa configuração se None)
            timeout: Timeout das requisições em segundos
        """
        self.base_url = (base_url or config.api.base_url).rstrip('/')
        self.timeout = timeout or config.api.timeout
        self.headers = config.api.headers.copy()
        
        self.session: Optional[ClientSession] = None
        self.logger = logger.bind(component="APIClient")
        
        # Estatísticas de uso
        self.stats = {
            "requests_made": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "data_sent": 0,
            "last_request_time": None
        }
    
    async def __aenter__(self):
        """Context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Garante que a sessão HTTP está ativa"""
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=self.timeout)
            self.session = ClientSession(
                timeout=timeout,
                headers=self.headers,
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
            )
    
    async def close(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, asyncio.TimeoutError))
    )
    async def _make_request(self, 
                           method: str, 
                           endpoint: str, 
                           data: Any = None,
                           params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Faz uma requisição HTTP com retry automático.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (sem base URL)
            data: Dados para enviar no body
            params: Parâmetros da query string
            
        Returns:
            Resposta da API em formato JSON
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        
        self.logger.debug(f"{method} {url}")
        self.stats["requests_made"] += 1
        self.stats["last_request_time"] = datetime.now()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                params=params
            ) as response:
                
                # Log da resposta
                self.logger.debug(f"Response: {response.status} {response.reason}")
                
                if response.status >= 400:
                    error_text = await response.text()
                    self.logger.error(f"API Error {response.status}: {error_text}")
                    self.stats["requests_failed"] += 1
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
                
                self.stats["requests_successful"] += 1
                
                # Tentar parse JSON
                try:
                    return await response.json()
                except Exception:
                    # Se não for JSON, retornar texto
                    text = await response.text()
                    return {"message": text, "status": response.status}
                    
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            self.stats["requests_failed"] += 1
            raise
    
    async def check_health(self) -> bool:
        """
        Verifica se a API está saudável.
        
        Returns:
            True se API está respondendo
        """
        try:
            response = await self._make_request("GET", config.api.endpoints["health"])
            return response.get("status") == "UP" or "status" in response
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False
    
    async def send_courses(self, courses: List[Course]) -> Dict[str, Any]:
        """
        Envia lista de cursos para a API.
        
        Args:
            courses: Lista de cursos coletados
            
        Returns:
            Resposta da API com estatísticas de processamento
        """
        if not courses:
            return {"message": "No courses to send", "count": 0}
        
        self.logger.info(f"Enviando {len(courses)} cursos para a API")
        
        try:
            # Converter para formato esperado pela API
            courses_data = [self._convert_course_to_api_format(course) for course in courses]
            
            # Enviar em lotes se necessário
            batch_size = 50
            results = []
            
            for i in range(0, len(courses_data), batch_size):
                batch = courses_data[i:i + batch_size]
                
                try:
                    result = await self._make_request(
                        "POST", 
                        config.api.endpoints["courses"], 
                        {"courses": batch}
                    )
                    results.append(result)
                    self.stats["data_sent"] += len(batch)
                    
                    # Pequeno delay entre lotes
                    if i + batch_size < len(courses_data):
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    self.logger.error(f"Erro ao enviar lote de cursos: {e}")
            
            # Consolidar resultados
            total_sent = sum(r.get("processed", 0) for r in results)
            total_errors = sum(r.get("errors", 0) for r in results)
            
            self.logger.info(f"Cursos enviados: {total_sent} sucessos, {total_errors} erros")
            
            return {
                "total_sent": total_sent,
                "total_errors": total_errors,
                "batches": len(results),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar cursos: {e}")
            raise
    
    async def send_schedules(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """
        Envia lista de horários para a API.
        
        Args:
            schedules: Lista de horários coletados
            
        Returns:
            Resposta da API com estatísticas de processamento
        """
        if not schedules:
            return {"message": "No schedules to send", "count": 0}
        
        self.logger.info(f"Enviando {len(schedules)} horários para a API")
        
        try:
            schedules_data = [self._convert_schedule_to_api_format(schedule) for schedule in schedules]
            
            result = await self._make_request(
                "POST", 
                config.api.endpoints["schedules"], 
                {"schedules": schedules_data}
            )
            
            self.stats["data_sent"] += len(schedules)
            
            self.logger.info(f"Horários enviados: {result.get('processed', 0)} sucessos")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar horários: {e}")
            raise
    
    async def send_professors(self, professors: List[Professor]) -> Dict[str, Any]:
        """
        Envia lista de professores para a API.
        
        Args:
            professors: Lista de professores coletados
            
        Returns:
            Resposta da API com estatísticas de processamento
        """
        if not professors:
            return {"message": "No professors to send", "count": 0}
        
        self.logger.info(f"Enviando {len(professors)} professores para a API")
        
        try:
            professors_data = [self._convert_professor_to_api_format(prof) for prof in professors]
            
            result = await self._make_request(
                "POST", 
                config.api.endpoints["professors"], 
                {"professors": professors_data}
            )
            
            self.stats["data_sent"] += len(professors)
            
            self.logger.info(f"Professores enviados: {result.get('processed', 0)} sucessos")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar professores: {e}")
            raise
    
    async def send_syllabi(self, syllabi: List[SyllabusData]) -> Dict[str, Any]:
        """
        Envia lista de ementas para a API.
        
        Args:
            syllabi: Lista de ementas coletadas
            
        Returns:
            Resposta da API com estatísticas de processamento
        """
        if not syllabi:
            return {"message": "No syllabi to send", "count": 0}
        
        self.logger.info(f"Enviando {len(syllabi)} ementas para a API")
        
        try:
            syllabi_data = [self._convert_syllabus_to_api_format(syllabus) for syllabus in syllabi]
            
            result = await self._make_request(
                "POST", 
                config.api.endpoints["syllabi"], 
                {"syllabi": syllabi_data}
            )
            
            self.stats["data_sent"] += len(syllabi)
            
            self.logger.info(f"Ementas enviadas: {result.get('processed', 0)} sucessos")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar ementas: {e}")
            raise
    
    async def send_mixed_data(self, data: List[BaseScrapedData]) -> Dict[str, Any]:
        """
        Envia dados mistos (diferentes tipos) para a API.
        
        Args:
            data: Lista de dados coletados (vários tipos)
            
        Returns:
            Resposta consolidada da API
        """
        if not data:
            return {"message": "No data to send", "count": 0}
        
        # Separar dados por tipo
        courses = [item for item in data if isinstance(item, Course)]
        schedules = [item for item in data if isinstance(item, Schedule)]
        professors = [item for item in data if isinstance(item, Professor)]
        syllabi = [item for item in data if isinstance(item, SyllabusData)]
        
        results = {}
        
        # Enviar cada tipo separadamente
        if courses:
            results["courses"] = await self.send_courses(courses)
        
        if schedules:
            results["schedules"] = await self.send_schedules(schedules)
        
        if professors:
            results["professors"] = await self.send_professors(professors)
        
        if syllabi:
            results["syllabi"] = await self.send_syllabi(syllabi)
        
        # Consolidar estatísticas
        total_sent = sum(
            result.get("total_sent", result.get("processed", 0)) 
            for result in results.values()
        )
        
        self.logger.info(f"Dados mistos enviados: {total_sent} itens em {len(results)} tipos")
        
        return {
            "total_items": len(data),
            "total_sent": total_sent,
            "by_type": results
        }
    
    def _convert_course_to_api_format(self, course: Course) -> Dict[str, Any]:
        """
        Converte Course para formato esperado pela API.
        
        Args:
            course: Objeto Course
            
        Returns:
            Dicionário no formato da API
        """
        return {
            "courseCode": course.course_code,
            "courseName": course.course_name,
            "credits": course.credits,
            "workload": course.workload,
            "department": course.department,
            "semester": course.semester,
            "prerequisites": course.prerequisites,
            "description": course.description,
            "scrapedAt": course.scraped_at.isoformat(),
            "sourceUrl": course.source_url
        }
    
    def _convert_schedule_to_api_format(self, schedule: Schedule) -> Dict[str, Any]:
        """
        Converte Schedule para formato esperado pela API.
        
        Args:
            schedule: Objeto Schedule
            
        Returns:
            Dicionário no formato da API
        """
        return {
            "courseCode": schedule.course_code,
            "classCode": schedule.class_code,
            "professor": schedule.professor,
            "scheduleText": schedule.schedule_text,
            "classroom": schedule.classroom,
            "semester": schedule.semester,
            "maxStudents": schedule.max_students,
            "enrolledStudents": schedule.enrolled_students,
            "daysOfWeek": schedule.days_of_week,
            "startTime": schedule.start_time.isoformat() if schedule.start_time else None,
            "endTime": schedule.end_time.isoformat() if schedule.end_time else None,
            "scrapedAt": schedule.scraped_at.isoformat(),
            "sourceUrl": schedule.source_url
        }
    
    def _convert_professor_to_api_format(self, professor: Professor) -> Dict[str, Any]:
        """
        Converte Professor para formato esperado pela API.
        
        Args:
            professor: Objeto Professor
            
        Returns:
            Dicionário no formato da API
        """
        return {
            "name": professor.name,
            "email": professor.email,
            "department": professor.department,
            "coursesTaught": professor.courses_taught,
            "researchAreas": professor.research_areas,
            "lattesUrl": professor.lattes_url,
            "scrapedAt": professor.scraped_at.isoformat(),
            "sourceUrl": professor.source_url
        }
    
    def _convert_syllabus_to_api_format(self, syllabus: SyllabusData) -> Dict[str, Any]:
        """
        Converte SyllabusData para formato esperado pela API.
        
        Args:
            syllabus: Objeto SyllabusData
            
        Returns:
            Dicionário no formato da API
        """
        return {
            "courseCode": syllabus.course_code,
            "courseName": syllabus.course_name,
            "objectives": syllabus.objectives,
            "syllabusContent": syllabus.syllabus_content,
            "methodology": syllabus.methodology,
            "evaluationCriteria": syllabus.evaluation_criteria,
            "bibliography": syllabus.bibliography,
            "competencies": syllabus.competencies,
            "pdfUrl": syllabus.pdf_url,
            "extractionConfidence": syllabus.extraction_confidence,
            "scrapedAt": syllabus.scraped_at.isoformat(),
            "sourceUrl": syllabus.source_url
        }
    
    async def get_existing_courses(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de cursos já existentes na API.
        
        Returns:
            Lista de cursos existentes
        """
        try:
            response = await self._make_request("GET", config.api.endpoints["courses"])
            return response.get("courses", response.get("data", []))
        except Exception as e:
            self.logger.error(f"Erro ao obter cursos existentes: {e}")
            return []
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Obtém status de sincronização da API.
        
        Returns:
            Informações sobre último sync e estatísticas
        """
        try:
            response = await self._make_request("GET", "/api/v1/sync/status")
            return response
        except Exception as e:
            self.logger.warning(f"Erro ao obter status de sync: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def get_client_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cliente HTTP.
        
        Returns:
            Dicionário com estatísticas de uso
        """
        return {
            **self.stats,
            "success_rate": (self.stats["requests_successful"] / 
                           max(self.stats["requests_made"], 1)) * 100,
            "base_url": self.base_url,
            "session_active": self.session is not None and not self.session.closed
        }
    
    def reset_stats(self):
        """Reseta estatísticas do cliente"""
        self.stats = {
            "requests_made": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "data_sent": 0,
            "last_request_time": None
        }


class SyncOrchestrator:
    """
    Orquestrador para sincronização completa de dados com a API.
    
    Coordena o envio de diferentes tipos de dados e monitora
    o progresso da sincronização.
    """
    
    def __init__(self, api_client: APIClient = None):
        """
        Inicializa o orquestrador.
        
        Args:
            api_client: Cliente da API (cria um novo se None)
        """
        self.api_client = api_client or APIClient()
        self.logger = logger.bind(component="SyncOrchestrator")
        
        self.sync_session = {
            "started_at": None,
            "completed_at": None,
            "status": "idle",
            "results": {},
            "errors": []
        }
    
    async def sync_all_data(self, 
                           courses: List[Course] = None,
                           schedules: List[Schedule] = None,
                           professors: List[Professor] = None,
                           syllabi: List[SyllabusData] = None) -> Dict[str, Any]:
        """
        Sincroniza todos os dados fornecidos com a API.
        
        Args:
            courses: Lista de cursos para sincronizar
            schedules: Lista de horários para sincronizar
            professors: Lista de professores para sincronizar
            syllabi: Lista de ementas para sincronizar
            
        Returns:
            Relatório completo da sincronização
        """
        self.sync_session["started_at"] = datetime.now()
        self.sync_session["status"] = "running"
        self.sync_session["results"] = {}
        self.sync_session["errors"] = []
        
        self.logger.info("Iniciando sincronização completa de dados")
        
        try:
            # Verificar saúde da API
            if not await self.api_client.check_health():
                raise Exception("API não está saudável")
            
            # Sincronizar cada tipo de dado
            if courses:
                self.logger.info(f"Sincronizando {len(courses)} cursos")
                self.sync_session["results"]["courses"] = await self.api_client.send_courses(courses)
            
            if professors:
                self.logger.info(f"Sincronizando {len(professors)} professores")
                self.sync_session["results"]["professors"] = await self.api_client.send_professors(professors)
            
            if schedules:
                self.logger.info(f"Sincronizando {len(schedules)} horários")
                self.sync_session["results"]["schedules"] = await self.api_client.send_schedules(schedules)
            
            if syllabi:
                self.logger.info(f"Sincronizando {len(syllabi)} ementas")
                self.sync_session["results"]["syllabi"] = await self.api_client.send_syllabi(syllabi)
            
            self.sync_session["status"] = "completed"
            self.sync_session["completed_at"] = datetime.now()
            
            # Calcular estatísticas finais
            total_sent = sum(
                result.get("total_sent", result.get("processed", 0))
                for result in self.sync_session["results"].values()
            )
            
            duration = (self.sync_session["completed_at"] - self.sync_session["started_at"]).total_seconds()
            
            self.logger.info(f"Sincronização completa: {total_sent} itens em {duration:.1f}s")
            
            return {
                "status": "success",
                "duration_seconds": duration,
                "total_items_sent": total_sent,
                "results_by_type": self.sync_session["results"],
                "api_stats": self.api_client.get_client_stats()
            }
            
        except Exception as e:
            self.sync_session["status"] = "failed"
            self.sync_session["completed_at"] = datetime.now()
            self.sync_session["errors"].append(str(e))
            
            self.logger.error(f"Sincronização falhou: {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "partial_results": self.sync_session["results"],
                "errors": self.sync_session["errors"]
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Retorna status atual da sincronização.
        
        Returns:
            Informações sobre a sessão de sincronização
        """
        return {
            **self.sync_session,
            "started_at": self.sync_session["started_at"].isoformat() if self.sync_session["started_at"] else None,
            "completed_at": self.sync_session["completed_at"].isoformat() if self.sync_session["completed_at"] else None
        }


# Instância global do cliente da API
api_client = APIClient()

# Instância global do orquestrador
sync_orchestrator = SyncOrchestrator(api_client)