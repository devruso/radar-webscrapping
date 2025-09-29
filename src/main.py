"""
API FastAPI para orquestração e controle dos web scrapers.

Esta API fornece endpoints para:
1. Executar scrapers individuais ou em lote
2. Monitorar progresso e status dos jobs
3. Gerenciar configurações e parâmetros
4. Visualizar estatísticas e logs
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..models.scraped_data import ScrapingJob, ScrapingType, ScrapingStatus, BaseScrapedData
from ..scrapers.base_scraper import scraper_registry
from ..scrapers.course_scraper import CourseScraper
from ..scrapers.schedule_scraper import ScheduleScraper
from ..scrapers.syllabus_scraper import SyllabusScraper
from ..services.api_client import api_client, sync_orchestrator
from ..utils.browser_manager import browser_manager
from ..config.settings import config


# Modelos Pydantic para API
class ScrapingRequest(BaseModel):
    """Modelo para requisição de scraping"""
    scraping_type: ScrapingType
    config: Dict[str, Any] = Field(default_factory=dict)
    send_to_backend: bool = Field(default=True, description="Enviar dados para o backend automaticamente")


class BatchScrapingRequest(BaseModel):
    """Modelo para requisição de scraping em lote"""
    scraping_types: List[ScrapingType]
    config: Dict[str, Any] = Field(default_factory=dict)
    send_to_backend: bool = Field(default=True)
    max_concurrent: int = Field(default=2, ge=1, le=5)


class JobResponse(BaseModel):
    """Modelo para resposta de job"""
    job_id: str
    scraping_type: ScrapingType
    status: ScrapingStatus
    message: str


class JobStatus(BaseModel):
    """Modelo para status detalhado do job"""
    job: ScrapingJob
    results: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)


# Armazenamento em memória para jobs (em produção, usar Redis ou banco)
active_jobs: Dict[str, ScrapingJob] = {}
job_results: Dict[str, List[BaseScrapedData]] = {}
job_logs: Dict[str, List[str]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup: registrar scrapers e inicializar browser
    scraper_registry.register(CourseScraper)
    scraper_registry.register(ScheduleScraper)
    scraper_registry.register(SyllabusScraper)
    
    await browser_manager.start()
    
    yield
    
    # Shutdown: limpar recursos
    await browser_manager.stop()
    await api_client.close()


# Criar aplicação FastAPI
app = FastAPI(
    title="Radar Web Scraping API",
    description="API para orquestrar e monitorar web scrapers do projeto Radar",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "name": "Radar Web Scraping API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "available_scrapers": list(scraper_registry.list_available_scrapers().keys()),
        "config": {
            "browser_headless": config.browser.headless,
            "rate_limit": config.browser.rate_limit,
            "api_backend_url": config.api.base_url
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Verificar componentes críticos
    browser_ok = browser_manager.browser is not None
    backend_ok = await api_client.check_health()
    
    status = "healthy" if browser_ok and backend_ok else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "browser": "ok" if browser_ok else "error",
            "backend_api": "ok" if backend_ok else "error"
        }
    }


@app.get("/scrapers")
async def list_scrapers():
    """Lista scrapers disponíveis"""
    return {
        "available_scrapers": scraper_registry.list_available_scrapers(),
        "count": len(scraper_registry.list_available_scrapers())
    }


@app.post("/scraping/start", response_model=JobResponse)
async def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Inicia um job de scraping específico
    """
    # Criar job ID único
    job_id = str(uuid.uuid4())
    
    # Criar job
    job = ScrapingJob(
        job_id=job_id,
        scraping_type=request.scraping_type,
        config=request.config
    )
    
    # Armazenar job
    active_jobs[job_id] = job
    job_results[job_id] = []
    job_logs[job_id] = []
    
    # Executar scraping em background
    background_tasks.add_task(
        execute_scraping_job, 
        job_id, 
        request.scraping_type, 
        request.config,
        request.send_to_backend
    )
    
    return JobResponse(
        job_id=job_id,
        scraping_type=request.scraping_type,
        status=ScrapingStatus.PENDING,
        message="Job criado e será executado em background"
    )


@app.post("/scraping/batch", response_model=List[JobResponse])
async def start_batch_scraping(request: BatchScrapingRequest, background_tasks: BackgroundTasks):
    """
    Inicia múltiplos jobs de scraping em lote
    """
    job_responses = []
    
    for scraping_type in request.scraping_types:
        job_id = str(uuid.uuid4())
        
        job = ScrapingJob(
            job_id=job_id,
            scraping_type=scraping_type,
            config=request.config
        )
        
        active_jobs[job_id] = job
        job_results[job_id] = []
        job_logs[job_id] = []
        
        job_responses.append(JobResponse(
            job_id=job_id,
            scraping_type=scraping_type,
            status=ScrapingStatus.PENDING,
            message="Job criado para execução em lote"
        ))
    
    # Executar batch em background
    background_tasks.add_task(
        execute_batch_scraping,
        [resp.job_id for resp in job_responses],
        request.scraping_types,
        request.config,
        request.send_to_backend,
        request.max_concurrent
    )
    
    return job_responses


@app.get("/scraping/jobs")
async def list_jobs(
    status: Optional[ScrapingStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados")
):
    """
    Lista jobs de scraping
    """
    jobs = list(active_jobs.values())
    
    # Filtrar por status se especificado
    if status:
        jobs = [job for job in jobs if job.status == status]
    
    # Ordenar por data de criação (mais recentes primeiro)
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Aplicar limite
    jobs = jobs[:limit]
    
    return {
        "jobs": [job.dict() for job in jobs],
        "total": len(jobs),
        "active_count": len([j for j in active_jobs.values() if j.status == ScrapingStatus.RUNNING])
    }


@app.get("/scraping/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Obtém status detalhado de um job específico
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = active_jobs[job_id]
    results = job_results.get(job_id, [])
    logs = job_logs.get(job_id, [])
    
    # Converter resultados para dict
    results_dict = []
    for result in results:
        if hasattr(result, 'dict'):
            results_dict.append(result.dict())
        else:
            results_dict.append(str(result))
    
    return JobStatus(
        job=job,
        results=results_dict,
        logs=logs
    )


@app.delete("/scraping/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancela um job de scraping
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = active_jobs[job_id]
    
    if job.status == ScrapingStatus.RUNNING:
        job.status = ScrapingStatus.CANCELLED
        job.completed_at = datetime.now()
        
        return {"message": f"Job {job_id} cancelado", "status": "cancelled"}
    else:
        return {"message": f"Job {job_id} não pode ser cancelado (status: {job.status})", "status": job.status}


@app.get("/scraping/results/{job_id}")
async def get_job_results(job_id: str):
    """
    Obtém resultados de um job específico
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = active_jobs[job_id]
    results = job_results.get(job_id, [])
    
    return {
        "job_id": job_id,
        "status": job.status,
        "results_count": len(results),
        "results": [result.dict() if hasattr(result, 'dict') else str(result) for result in results]
    }


@app.get("/stats")
async def get_system_stats():
    """
    Obtém estatísticas do sistema
    """
    # Estatísticas dos jobs
    job_stats = {
        "total_jobs": len(active_jobs),
        "by_status": {},
        "by_type": {}
    }
    
    for job in active_jobs.values():
        # Por status
        status_key = job.status.value
        job_stats["by_status"][status_key] = job_stats["by_status"].get(status_key, 0) + 1
        
        # Por tipo
        type_key = job.scraping_type.value
        job_stats["by_type"][type_key] = job_stats["by_type"].get(type_key, 0) + 1
    
    # Estatísticas dos componentes
    api_stats = api_client.get_client_stats() if hasattr(api_client, 'get_client_stats') else {}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "jobs": job_stats,
        "api_client": api_stats,
        "system": {
            "active_scrapers": len(scraper_registry.list_available_scrapers()),
            "browser_active": browser_manager.browser is not None
        }
    }


@app.post("/sync/all")
async def sync_all_data(background_tasks: BackgroundTasks):
    """
    Executa sincronização completa de todos os dados com o backend
    """
    # Coletar todos os resultados disponíveis
    all_results = []
    for results in job_results.values():
        all_results.extend(results)
    
    if not all_results:
        return {"message": "Nenhum dado disponível para sincronização", "count": 0}
    
    # Separar por tipo
    from ..models.scraped_data import Course, Schedule, Professor, SyllabusData
    
    courses = [r for r in all_results if isinstance(r, Course)]
    schedules = [r for r in all_results if isinstance(r, Schedule)]
    professors = [r for r in all_results if isinstance(r, Professor)]
    syllabi = [r for r in all_results if isinstance(r, SyllabusData)]
    
    # Executar sincronização em background
    sync_job_id = str(uuid.uuid4())
    background_tasks.add_task(
        execute_full_sync,
        sync_job_id,
        courses,
        schedules,
        professors,
        syllabi
    )
    
    return {
        "message": "Sincronização iniciada",
        "sync_job_id": sync_job_id,
        "data_summary": {
            "courses": len(courses),
            "schedules": len(schedules),
            "professors": len(professors),
            "syllabi": len(syllabi),
            "total": len(all_results)
        }
    }


# Funções auxiliares para execução em background

async def execute_scraping_job(job_id: str, 
                              scraping_type: ScrapingType, 
                              config: Dict[str, Any],
                              send_to_backend: bool):
    """
    Executa um job de scraping individual
    """
    job = active_jobs[job_id]
    
    try:
        # Criar instância do scraper
        scraper = scraper_registry.create_scraper(scraping_type)
        if not scraper:
            raise Exception(f"Scraper não encontrado para tipo: {scraping_type}")
        
        # Executar scraping
        results = await scraper.scrape_with_job_tracking(job, config)
        
        # Armazenar resultados
        job_results[job_id] = results
        job_logs[job_id].append(f"Scraping concluído: {len(results)} itens coletados")
        
        # Enviar para backend se solicitado
        if send_to_backend and results:
            try:
                await api_client.send_mixed_data(results)
                job_logs[job_id].append(f"Dados enviados para backend: {len(results)} itens")
            except Exception as e:
                job_logs[job_id].append(f"Erro ao enviar para backend: {e}")
                
    except Exception as e:
        job.status = ScrapingStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now()
        job_logs[job_id].append(f"Erro no scraping: {e}")


async def execute_batch_scraping(job_ids: List[str],
                                scraping_types: List[ScrapingType],
                                config: Dict[str, Any],
                                send_to_backend: bool,
                                max_concurrent: int):
    """
    Executa múltiplos jobs de scraping em lote
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_single_job(job_id: str, scraping_type: ScrapingType):
        async with semaphore:
            await execute_scraping_job(job_id, scraping_type, config, send_to_backend)
    
    # Executar jobs concorrentemente
    tasks = [execute_single_job(job_id, scraping_type) 
             for job_id, scraping_type in zip(job_ids, scraping_types)]
    
    await asyncio.gather(*tasks, return_exceptions=True)


async def execute_full_sync(sync_job_id: str,
                           courses: List,
                           schedules: List,
                           professors: List,
                           syllabi: List):
    """
    Executa sincronização completa com o backend
    """
    try:
        result = await sync_orchestrator.sync_all_data(
            courses=courses,
            schedules=schedules,
            professors=professors,
            syllabi=syllabi
        )
        
        # Log do resultado (em uma implementação real, seria salvo em banco)
        print(f"Sincronização {sync_job_id} concluída: {result}")
        
    except Exception as e:
        print(f"Erro na sincronização {sync_job_id}: {e}")


# Função para executar a API
def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Executa a API FastAPI
    
    Args:
        host: Host para bind
        port: Porta para bind
        reload: Se deve recarregar automaticamente em mudanças
    """
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_api(reload=True)