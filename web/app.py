"""
Servidor REST API e Interface da Central Inteligente de Shorts (FastAPI).
Plataforma Multi-Skill AI Content Company: 10 Agentes Especializados, 20 Canais,
Google Drive 5 TB, Deep Podcast Analyzer, Biblioteca 50.000+ e Perfis Editoriais.
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
from core.large_scale_cataloger import LargeScaleCataloger
from core.podcast_deep_analyzer import PodcastDeepAnalyzer
from core.editorial_profiles import EditorialProfilesManager
from core.experimentation import ExperimentationLab

app = FastAPI(
    title="Central Inteligente de Shorts - Multi-Skill AI Content Company",
    description="Empresa de Inteligência Artificial Multimodal com 10 Especialistas, 20 Canais e Drive 5 TB",
    version="2.5.0"
)

# Inicializa banco de dados e perfis
init_db()
profiles_mgr = EditorialProfilesManager()
profiles_mgr.init_profiles()

# Inicializa gerenciadores e motores
gdrive_mgr = GDriveManager()
channel_mgr = ChannelManager()
cataloger = ReferenceCataloger()
intelligence_engine = IntelligenceEngine()
script_gen = ScriptGenerator()
memory = CentralMemory()
company = ContentCompany(memory=memory)
large_cataloger = LargeScaleCataloger(memory=memory)
podcast_analyzer = PodcastDeepAnalyzer(memory=memory)
exp_lab = ExperimentationLab(memory=memory)

# ------------------------------------------------------------------------------
# 1. VISÃO GERAL & KPIs
# ------------------------------------------------------------------------------
@app.get("/api/overview")
def get_overview_kpis():
    """Retorna o painel consolidado de métricas e status dos 20 canais e Drive 5TB."""
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

    return {
        "kpis": {
            "cataloged_references": total_cataloged,
            "target_references": 50000,
            "catalog_progress_percent": round((total_cataloged / 50000) * 100, 2),
            "content_patterns_mined": total_patterns,
            "scripts_generated": total_scripts,
            "podcast_cuts_evaluated": total_cuts,
            "agent_decisions_logged": total_decisions,
            "active_experiments": total_experiments,
            "videos_in_production": in_production,
            "videos_published": total_published,
            "active_channels": 20,
            "specialist_agents": 10
        },
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
            detail="Google Drive não autenticado. Execute 'CONECTAR MEU GOOGLE DRIVE.bat' na sua Área de Trabalho."
        )
    folders = gdrive_mgr.setup_drive_structure()
    return {"message": "Pastas sincronizadas no Google Drive 5 TB com sucesso!", "folders": folders}

# ------------------------------------------------------------------------------
# 3. OS 10 AGENTES ESPECIALIZADOS & MESA REDONDA
# ------------------------------------------------------------------------------
@app.get("/api/agents")
def list_agents():
    """Retorna os 10 especialistas da empresa, seus papéis e critérios técnicos."""
    return company.get_company_roster()

@app.get("/api/agents/decisions")
def list_agent_decisions(agent_name: Optional[str] = None, limit: int = 50):
    """Histórico de decisões e deliberações registradas pelos agentes."""
    return memory.get_agent_history(agent_name, limit)

class CutEvaluationRequest(BaseModel):
    title: str
    transcript: str
    duration: float = 35.0
    is_direct_clip: bool = True
    source_authorized: bool = True

@app.post("/api/agents/evaluate")
def evaluate_cut_with_company(req: CutEvaluationRequest):
    """Executa a deliberação dos 10 agentes e do Diretor de Conteúdo sobre um trecho."""
    payload = {
        "title": req.title,
        "transcript": req.transcript,
        "duration": req.duration,
        "is_direct_clip": req.is_direct_clip,
        "source_authorized": req.source_authorized
    }
    return company.evaluate_candidate_cut(payload)

# ------------------------------------------------------------------------------
# 4. DEEP PODCAST ANALYZER
# ------------------------------------------------------------------------------
class PodcastAnalysisRequest(BaseModel):
    title: str
    transcript_text: str
    source_url: Optional[str] = ""
    channel_name: Optional[str] = "Podcast Host"

@app.post("/api/podcasts/analyze")
def analyze_podcast_endpoint(req: PodcastAnalysisRequest):
    """Ingere episódio longo, segmenta em candidatos e executa a deliberação dos 10 agentes."""
    res = podcast_analyzer.analyze_episode(
        episode_title=req.title,
        transcript_data=req.transcript_text,
        source_url=req.source_url or "",
        channel_name=req.channel_name or "Podcast Host"
    )
    return res

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
# 5. PERSONALIDADES EDITORIAIS
# ------------------------------------------------------------------------------
@app.get("/api/profiles")
def list_editorial_profiles():
    return profiles_mgr.get_all_profiles()

class BlendProfileRequest(BaseModel):
    slug_a: str
    slug_b: str
    weight_a: float = 0.5

@app.post("/api/profiles/blend")
def blend_profiles_endpoint(req: BlendProfileRequest):
    return profiles_mgr.blend_profiles(req.slug_a, req.slug_b, req.weight_a)

# ------------------------------------------------------------------------------
# 6. LABORATÓRIO DE EXPERIMENTOS A/B
# ------------------------------------------------------------------------------
@app.get("/api/experiments")
def list_experiments_endpoint():
    return exp_lab.list_experiments()

class CreateExperimentRequest(BaseModel):
    title: str
    hypothesis: str
    variable_type: str
    control_variant: str
    test_variant: str
    channel_id: int

@app.post("/api/experiments")
def create_experiment_endpoint(req: CreateExperimentRequest):
    exp_id = exp_lab.create_experiment(
        title=req.title,
        hypothesis=req.hypothesis,
        variable_type=req.variable_type,
        control_variant=req.control_variant,
        test_variant=req.test_variant,
        channel_id=req.channel_id
    )
    return {"experiment_id": exp_id, "status": "running"}

class RecordExperimentResultRequest(BaseModel):
    control_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]

@app.post("/api/experiments/{experiment_id}/record")
def record_experiment_endpoint(experiment_id: int, req: RecordExperimentResultRequest):
    return exp_lab.record_experiment_results(
        experiment_id=experiment_id,
        control_metrics=req.control_metrics,
        test_metrics=req.test_metrics
    )

# ------------------------------------------------------------------------------
# 7. BIBLIOTECA DE REFERÊNCIAS (50.000 VÍDEOS)
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

class IngestUrlRequest(BaseModel):
    url: str
    category_slug: str = "cortes_podcasts"
    transcript: Optional[str] = ""

@app.post("/api/catalog/ingest")
def ingest_reference_url(req: IngestUrlRequest):
    return large_cataloger.ingest_reference(req.url, req.category_slug, req.transcript or "")

# ------------------------------------------------------------------------------
# 8. OS 20 CANAIS YOUTUBE SHORTS
# ------------------------------------------------------------------------------
@app.get("/api/channels")
def list_channels():
    return channel_mgr.list_all_channels()

@app.get("/api/channels/{channel_id}")
def get_channel(channel_id: int):
    ch = channel_mgr.get_channel_by_id(channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Canal não encontrado.")
    return ch

# ------------------------------------------------------------------------------
# 9. ROTEIROS & IDEIAS 100% ORIGINAIS
# ------------------------------------------------------------------------------
@app.get("/api/scripts")
def list_scripts(channel_id: Optional[int] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT s.*, c.name as channel_name 
            FROM scripts s
            LEFT JOIN channels c ON c.id = s.channel_id
        """
        params = []
        if channel_id:
            query += " WHERE s.channel_id = ?"
            params.append(channel_id)
        query += " ORDER BY s.id DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

class GenerateScriptRequest(BaseModel):
    channel_id: int
    topic: str
    target_archetype: Optional[str] = "curiosidade"

@app.post("/api/scripts/generate")
def generate_script(req: GenerateScriptRequest):
    res = script_gen.generate_original_script(req.channel_id, req.topic, req.target_archetype)
    if not res:
        raise HTTPException(status_code=500, detail="Erro ao gerar roteiro.")
    return res

# ------------------------------------------------------------------------------
# 10. CATEGORIAS DISPONÍVEIS
# ------------------------------------------------------------------------------
@app.get("/api/categories")
def list_categories():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        return [dict(r) for r in cursor.fetchall()]

# ------------------------------------------------------------------------------
# 11. MEMÓRIA CENTRAL & PADRÕES
# ------------------------------------------------------------------------------
@app.get("/api/memory/stats")
def get_memory_stats():
    return memory.get_summary_stats()

@app.get("/api/memory/patterns")
def list_memory_patterns(category: Optional[str] = None):
    return memory.query_patterns(category_slug=category)

@app.get("/api/memory/nodes")
def list_knowledge_nodes(node_type: Optional[str] = None):
    return memory.query_knowledge_nodes(node_type=node_type)

# Servir arquivos estáticos do Dashboard Frontend
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "Central de Shorts API Online. Acesse /docs para Swagger."})
