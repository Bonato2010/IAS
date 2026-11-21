"""
Servidor REST API e Interface da Central Inteligente de Conteúdo (VIAGEM / IAS).
Plataforma Multi-Skill: 10 Agentes Especializados de Produção, Central Multiagente de Pesquisadores,
Pipeline de Pesquisa e Aprendizado (200.000+ Shorts), Módulo de Análise Crítica, Google Drive 5 TB e 20 Canais.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from database.db import get_db_connection, init_db
from core.gdrive_manager import GDriveManager
from core.channel_manager import ChannelManager
from core.cataloger import ReferenceCataloger
from core.intelligence_engine import IntelligenceEngine
from core.script_generator import ScriptGenerator
from memory.central_memory import CentralMemory
from agents.company import ContentCompany
from agents.research_agents import ResearchOrchestrator
from core.large_scale_cataloger import LargeScaleCataloger
from core.research_pipeline import ResearchPipelineManager
from core.critical_analysis import CriticalAnalysisEngine
from core.podcast_deep_analyzer import PodcastDeepAnalyzer
from core.editorial_profiles import EditorialProfilesManager
from core.experimentation import ExperimentationLab
from services.service_registry import ServiceRegistry
from services.orchestration.langgraph_engine import IASOrchestrationEngine
from services.semantic_memory.vector_memory import VectorMemoryService
from services.model_gateway.gateway import ModelGatewayService
from services.video_analysis.yt_metadata import VideoMetadataService

app = FastAPI(
    title="VIAGEM / IAS - Central de Inteligência de Conteúdo",
    description="Plataforma de IA com Central Multiagente de Pesquisa, Análise Crítica e Produção em Escala (200.000+ Shorts) com Drive 5 TB",
    version="3.0.0"
)

# Inicializações
init_db()
profiles_mgr = EditorialProfilesManager()
profiles_mgr.init_profiles()

gdrive_mgr = GDriveManager()
channel_mgr = ChannelManager()
cataloger = ReferenceCataloger()
intelligence_engine = IntelligenceEngine()
script_gen = ScriptGenerator()
memory = CentralMemory()
company = ContentCompany(memory=memory)
research_orchestrator = ResearchOrchestrator(memory=memory)
large_cataloger = LargeScaleCataloger(memory=memory)
pipeline_mgr = ResearchPipelineManager(memory=memory)
critical_analysis_eng = CriticalAnalysisEngine(memory=memory)
podcast_analyzer = PodcastDeepAnalyzer(memory=memory)
exp_lab = ExperimentationLab(memory=memory)

# Serviços de Infraestrutura Open Source
service_registry = ServiceRegistry()
orchestration_engine = IASOrchestrationEngine()
semantic_memory = VectorMemoryService()
model_gateway = ModelGatewayService()
video_metadata_svc = VideoMetadataService()

class StartWorkflowRequest(BaseModel):
    task_id: str
    target_id: str
    niche: str = "futebol"

class SemanticSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = 5

class UpdateStatusRequest(BaseModel):
    video_id: str
    new_status: str
    notes: Optional[str] = None

class CompletionRequest(BaseModel):
    prompt: str
    task: str = "critical_analysis"
    preferred_model: Optional[str] = None

# ------------------------------------------------------------------------------
# 1. VISÃO GERAL & KPIs (OPERACIONAL)
# ------------------------------------------------------------------------------
@app.get("/api/overview")
def get_overview_kpis():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM video_references")
        total_cataloged = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM content_patterns")
        total_patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scripts")
        total_scripts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM podcast_candidate_cuts")
        total_cuts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_decisions")
        total_decisions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM experiments")
        total_experiments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM production_pipeline WHERE current_stage != 'published'")
        in_production = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM publications WHERE status = 'published'")
        total_published = cursor.fetchone()[0]

    drive_quota = gdrive_mgr.get_storage_quota()
    pipeline_status = pipeline_mgr.get_pipeline_metrics()

    return {
        "kpis": {
            "cataloged_references": total_cataloged,
            "target_references": 200000,
            "catalog_progress_percent": round((total_cataloged / 200000.0) * 100, 3),
            "content_patterns_mined": total_patterns,
            "scripts_generated": total_scripts,
            "podcast_cuts_evaluated": total_cuts,
            "agent_decisions_logged": total_decisions,
            "active_experiments": total_experiments,
            "videos_in_production": in_production,
            "videos_published": total_published,
            "active_channels": 20,
            "specialist_agents": 10,
            "researcher_agents": 10
        },
        "pipeline_metrics": pipeline_status,
        "drive_storage": drive_quota
    }

# ------------------------------------------------------------------------------
# 2. GOOGLE DRIVE (5 TB)
# ------------------------------------------------------------------------------
@app.get("/api/drive/quota")
def get_drive_quota():
    return gdrive_mgr.get_storage_quota()

@app.post("/api/drive/setup-folders")
def setup_drive_folders():
    if not gdrive_mgr.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Google Drive não autenticado. Execute 'CONECTAR MEU GOOGLE DRIVE.bat' no Desktop."
        )
    folders = gdrive_mgr.setup_drive_structure()
    return {"message": "13 Pastas sincronizadas no Google Drive 5 TB com sucesso!", "folders": folders}

# ------------------------------------------------------------------------------
# 3. CENTRAL MULTIAGENTE DE PESQUISA (PESQUISADORES)
# ------------------------------------------------------------------------------
@app.get("/api/researchers")
def list_researchers():
    """Retorna a lista dos 10 pesquisadores autônomos por nicho."""
    return research_orchestrator.list_researchers()

class ResearcherRunRequest(BaseModel):
    niche_slug: str
    query: Optional[str] = None

@app.post("/api/researchers/run")
def run_researcher(req: ResearcherRunRequest):
    """Executa missão de pesquisa com o pesquisador especializado do nicho."""
    return research_orchestrator.execute_targeted_research(req.niche_slug, req.query)

@app.post("/api/researchers/sweep")
def run_global_sweep():
    """Dispara missão sincronizada em todos os 10 nichos simultaneamente."""
    return research_orchestrator.execute_global_sweep()

# ------------------------------------------------------------------------------
# 4. ALGORITMO DE PESQUISA & APRENDIZADO (200.000+ SHORTS)
# ------------------------------------------------------------------------------
@app.get("/api/pipeline/metrics")
def get_pipeline_metrics():
    return pipeline_mgr.get_pipeline_metrics()

class PipelineStepRequest(BaseModel):
    niche_slug: str
    query: str

@app.post("/api/pipeline/run-step")
def run_pipeline_step(req: PipelineStepRequest):
    return pipeline_mgr.run_full_pipeline_step(req.niche_slug, req.query)

# ------------------------------------------------------------------------------
# 5. MÓDULO DE ANÁLISE CRÍTICA PROFISSIONAL
# ------------------------------------------------------------------------------
class CriticalAnalysisRequest(BaseModel):
    title: str
    transcript: str
    duration_seconds: float = 35.0
    niche_slug: str = "geral"

@app.post("/api/critical-analysis")
def run_critical_analysis(req: CriticalAnalysisRequest):
    """Executa a Análise Crítica completa com justificativas técnicas detalhadas."""
    return critical_analysis_eng.evaluate_content(
        title=req.title,
        transcript=req.transcript,
        duration_seconds=req.duration_seconds,
        niche_slug=req.niche_slug
    )

# ------------------------------------------------------------------------------
# 6. OS 10 AGENTES ESPECIALIZADOS DE PRODUÇÃO
# ------------------------------------------------------------------------------
@app.get("/api/agents")
def list_agents():
    return company.get_company_roster()

@app.get("/api/agents/decisions")
def list_agent_decisions(agent_name: Optional[str] = None, limit: int = 50):
    return memory.get_agent_history(agent_name, limit)

class CutEvaluationRequest(BaseModel):
    title: str
    transcript: str
    duration: float = 35.0
    is_direct_clip: bool = True
    source_authorized: bool = True

@app.post("/api/agents/evaluate")
def evaluate_cut_with_company(req: CutEvaluationRequest):
    payload = {
        "title": req.title,
        "transcript": req.transcript,
        "duration": req.duration,
        "is_direct_clip": req.is_direct_clip,
        "source_authorized": req.source_authorized
    }
    return company.evaluate_candidate_cut(payload)

# ------------------------------------------------------------------------------
# 7. DEEP PODCAST ANALYZER
# ------------------------------------------------------------------------------
class PodcastAnalysisRequest(BaseModel):
    title: str
    transcript_text: str
    source_url: Optional[str] = ""
    channel_name: Optional[str] = "Podcast Host"

@app.post("/api/podcasts/analyze")
def analyze_podcast_endpoint(req: PodcastAnalysisRequest):
    return podcast_analyzer.analyze_episode(
        episode_title=req.title,
        transcript_data=req.transcript_text,
        source_url=req.source_url or "",
        channel_name=req.channel_name or "Podcast Host"
    )

@app.get("/api/podcasts/cuts")
def list_podcast_cuts(status: Optional[str] = None, limit: int = 50):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM podcast_candidate_cuts"
        params = []
        if status:
            query += " WHERE director_decision LIKE ?"
            params.append(f"%{status}%")
        query += " ORDER BY quality_score DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            if d.get("agent_evaluations"):
                try:
                    d["agent_evaluations"] = json.loads(d["agent_evaluations"])
                except Exception:
                    pass
            rows.append(d)
        return rows

# ------------------------------------------------------------------------------
# 8. BIBLIOTECA DE REFERÊNCIAS (200.000 SHORTS)
# ------------------------------------------------------------------------------
@app.get("/api/catalog")
def list_catalog_videos(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT v.*, c.name as category_name 
            FROM video_references v
            LEFT JOIN categories c ON c.id = v.category_id
            WHERE 1=1
        """
        params = []
        if category:
            query += " AND c.slug = ?"
            params.append(category)
        if search:
            query += " AND (v.title LIKE ? OR v.author LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY v.retention_score DESC, v.views_count DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

# ------------------------------------------------------------------------------
# 9. PERSONALIDADES EDITORIAIS & EXPERIMENTOS
# ------------------------------------------------------------------------------
@app.get("/api/profiles")
def list_editorial_profiles():
    return profiles_mgr.get_all_profiles()

@app.get("/api/experiments")
def list_experiments_endpoint():
    return exp_lab.list_experiments()

# ------------------------------------------------------------------------------
# 10. OS 20 CANAIS YOUTUBE SHORTS
# ------------------------------------------------------------------------------
@app.get("/api/channels")
def list_channels():
    return channel_mgr.list_all_channels()

@app.get("/api/categories")
def list_categories():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        return [dict(r) for r in cursor.fetchall()]

@app.get("/api/memory/stats")
def get_memory_stats():
    return memory.get_summary_stats()

@app.get("/api/memory/nodes")
def list_knowledge_nodes(node_type: Optional[str] = None):
    return memory.query_knowledge_nodes(node_type=node_type)

# ------------------------------------------------------------------------------
# 11. SERVIÇOS & INFRAESTRUTURA OPEN SOURCE (LangGraph, pgvector, LiteLLM, yt-dlp)
# ------------------------------------------------------------------------------
@app.get("/api/services/status")
def get_services_status():
    """Retorna telemetria e estado operacional das 7 tecnologias essenciais."""
    return service_registry.check_all()

@app.get("/api/services/costs")
def get_services_costs():
    """Retorna métricas de consumo de tokens e custos estimados via LiteLLM."""
    return model_gateway.get_usage_metrics()

@app.get("/api/orchestration/tasks")
def list_orchestration_tasks():
    """Lista todos os fluxos e tarefas registradas no LangGraph."""
    return orchestration_engine.list_all_tasks()

@app.get("/api/orchestration/task/{task_id}")
def get_orchestration_task(task_id: str):
    """Retorna estado e progresso das 12 etapas de uma tarefa específica."""
    state = orchestration_engine.get_task_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return state

@app.post("/api/orchestration/start")
def start_orchestration_flow(req: StartWorkflowRequest):
    """Inicia o pipeline LangGraph de 12 etapas com checkpoints."""
    state = orchestration_engine.start_workflow(
        task_id=req.task_id,
        target_id=req.target_id,
        niche=req.niche
    )
    return state

@app.post("/api/orchestration/approve/{task_id}")
def approve_orchestration_task(task_id: str):
    """Aprova a etapa 11 (revisão humana) e conclui a distribuição (etapa 12)."""
    resumed = orchestration_engine.approve_and_resume(task_id)
    if not resumed:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada para aprovação")
    return resumed

@app.post("/api/semantic/search")
def search_semantic_memory(req: SemanticSearchRequest):
    """Busca por significado e contexto vetorial (distância de cosseno)."""
    results = semantic_memory.search_similar(
        query=req.query,
        category=req.category,
        top_k=req.top_k
    )
    return {
        "query": req.query,
        "category": req.category,
        "count": len(results),
        "results": results
    }

@app.get("/api/semantic/stats")
def get_semantic_stats():
    """Retorna estatísticas da memória semântica vetorial."""
    return semantic_memory.get_stats()

@app.get("/api/approval/queue")
def get_approval_queue(status: Optional[str] = None):
    """Retorna vídeos na máquina de estados de catalogação e aprovação de direitos."""
    return video_metadata_svc.list_by_status(status=status)

@app.post("/api/approval/update-status")
def update_video_status(req: UpdateStatusRequest):
    """Avança o status de um vídeo na máquina de estados (catalogado -> aprovado)."""
    res = video_metadata_svc.advance_status(
        video_id=req.video_id,
        new_status=req.new_status,
        notes=req.notes
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.post("/api/gateway/completion")
def model_gateway_completion(req: CompletionRequest):
    """Executa requisição ao gateway LiteLLM com fallback automático multi-provedor."""
    messages = [{"role": "user", "content": req.prompt}]
    return model_gateway.completion(
        messages=messages,
        task=req.task,
        preferred_model=req.preferred_model
    )

# Servir Frontend
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "VIAGEM / IAS API Online."})
