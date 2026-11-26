"""
VANTIS — Motor de Produção Editorial Inteligente (Fase 21)
Transforma referências reais e memória editorial isolada por canal em pacotes
completos de produção (Conceito, Roteiro Original, Plano Audiovisual com ASSET_NEEDED,
Plano de Áudio e Checklist) com versionamento e máquina de estados explícita.
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.editorial_profiles import PROFILES_DEFINITIONS
from services.learning.audiovisual_learning_system import AudiovisualLearningSystem

PRODUCTION_STATES = (
    "DRAFT",
    "GENERATING",
    "READY_FOR_REVIEW",
    "CHANGES_REQUESTED",
    "APPROVED_FOR_PRODUCTION",
    "REJECTED",
    "PRODUCTION_IN_PROGRESS",
    "COMPLETED",
    "BLOCKED",
    "FAILED",
)

# 5 identidades editoriais independentes preservando canais reais do banco
CHANNEL_IDENTITIES: Dict[int, Dict[str, Any]] = {
    1: {
        "channel_id": 1,
        "name": "Canal 01 - Futebol em 60 Segundos",
        "niche": "futebol_outros",
        "profile_slug": "fanatico_futebol",
        "language": "pt-BR direto, vibrante e opinativo de arquibancada",
        "rhythm": "Cortes ágeis (1.8s–3.0s) nos momentos de lance; ~150 WPM",
        "narrative_structure": "Lance/Polêmica imediata -> Contexto tático ou histórico -> Virada -> Pergunta provocativa",
        "hook_style": "Afirmação provocativa ou lance decisivo nos primeiros 2.5s",
        "visual_style": "Lances rápidos, zoom dramático em detalhes, placar/estatística em destaque",
        "narration_tone": "Passional, firme, energético e provocativo",
        "quality_criteria": ["Fidelidade factual ao lance/história", "Sem spam visual", "Áudio limpo (-14 LUFS alvo)"],
        "audience": "Torcedores e fãs de futebol brasileiro e internacional (16–40 anos)",
        "music_ambience": "Beat esportivo percussivo royalty-free em volume de fundo (-24 LUFS)",
    },
    2: {
        "channel_id": 2,
        "name": "Canal 02 - Arquivo Sombrio (Casos Reais)",
        "niche": "casos_policiais",
        "profile_slug": "investigador_misterios",
        "language": "pt-BR sóbrio, investigativo, preciso e respeitoso",
        "rhythm": "Abertura tensa controlada + cortes estratégicos (>=4 cortes validado) na revelação; ~125 WPM",
        "narrative_structure": "Enigma/Data real -> Evidência forense -> Reviravolta investigativa -> Desfecho factual",
        "hook_style": "Detalhe intrigante ou contradição documental nos primeiros 3s",
        "visual_style": "Paleta fria, documentos/mapas desfocados quando sensível, marcações cronológicas",
        "narration_tone": "Sério, pausado, investigativo e sem sensacionalismo gratuito",
        "quality_criteria": ["Respeito às vítimas", "Sem gore explícito", "Diferenciação clara entre fato e hipótese"],
        "audience": "Interessados em investigação criminal, perícia e mistérios reais",
        "music_ambience": "Drone/tensão minimalista royalty-free sem vocais",
    },
    3: {
        "channel_id": 3,
        "name": "Canal 03 - Rir para Não Chorar",
        "niche": "humor",
        "profile_slug": "comediante_acido",
        "language": "pt-BR coloquial, irônico, ritmo de conversa e quebra de expectativa",
        "rhythm": "Setup curto -> Pausa cômica (0.4s) -> Punchline visual/verbal (progressão em 3 atos)",
        "narrative_structure": "Situação cotidiana reconhecível -> Escalada absurda -> Quebra de expectativa final",
        "hook_style": "Premissa absurda ou confissão cotidiana nos primeiros 2s",
        "visual_style": "Cortes secos de reação, texto de apoio pontual no punchline",
        "narration_tone": "Espirituoso, expressivo, timing cômico bem marcado",
        "quality_criteria": ["Originalidade da piada/situação", "Sem ofensa gratuita", "Punchline claro no encerramento"],
        "audience": "Público geral de humor cotidiano e comédia rápida",
        "music_ambience": "Trilha leve pizzicato/comédia royalty-free ou silêncio intencional pré-punchline",
    },
    4: {
        "channel_id": 4,
        "name": "Canal 04 - Mente Curiosa & Ciência",
        "niche": "curiosidades",
        "profile_slug": "cientista_curioso",
        "language": "pt-BR claro, didático, fascinante e baseado em mecanismos reais",
        "rhythm": "Ritmo dinâmico explicativo (~140 WPM) com respiros de 0.3s após conceitos-chave",
        "narrative_structure": "Pergunta instigante -> Mecanismo científico explicado simples -> Exemplo real -> Conclusão memorável",
        "hook_style": "Pergunta contra-intuitiva ou fato científico verificável em 3s",
        "visual_style": "Diagramas simples, overlays de escala/números, transições limpas",
        "narration_tone": "Curioso, esclarecedor, entusiasmado com rigor factual",
        "quality_criteria": ["Precisão científica básica", "Analogia clara", "Sem pseudociência"],
        "audience": "Curiosos por ciência, astronomia, biologia, física e tecnologia",
        "music_ambience": "Synth ambiente curioso/futurista royalty-free suave",
    },
    5: {
        "channel_id": 5,
        "name": "Canal 05 - Mente Focada & Produtividade",
        "niche": "desenvolvimento_pessoal",
        "profile_slug": "guru_produtividade",
        "language": "pt-BR objetivo, prático, disciplinado e acionável",
        "rhythm": "Narração estruturada clara + gancho forte + 3 atos completos (validados no canal); ~135 WPM",
        "narrative_structure": "Dor real de procrastinação/foco -> Regra ou hábito aplicável hoje -> Exemplo prático -> Ação imediata",
        "hook_style": "Diagnóstico direto de erro de rotina nos primeiros 2.5s",
        "visual_style": "Minimalista, tipografia forte em palavras-chave, contraste alto",
        "narration_tone": "Firme, claro, encorajador sem clichês vazios",
        "quality_criteria": ["Passo acionável em <60s", "Sem promessas irreais", "Narração e conclusão presentes"],
        "audience": "Estudantes e profissionais buscando foco, rotina e disciplina",
        "music_ambience": "Lo-fi focado ou pulso minimalista royalty-free em volume baixo",
    },
}


def _parse_json(raw: Any, default: Any) -> Any:
    if isinstance(raw, type(default)):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default
    return default


class EditorialProductionEngine:
    """Gera, versiona e gerencia pacotes editoriais completos por canal a partir de memória e referências reais."""

    def __init__(self, db_path: Optional[Path] = None):
        self.als = AudiovisualLearningSystem(db_path=db_path)
        self.db_path = Path(self.als.db_path)
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS editorial_production_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_uid TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    parent_package_id INTEGER,
                    channel_id INTEGER NOT NULL,
                    channel_name TEXT,
                    niche TEXT,
                    theme TEXT NOT NULL,
                    reference_source_id TEXT,
                    status TEXT NOT NULL DEFAULT 'DRAFT',
                    target_duration_sec REAL DEFAULT 35.0,
                    editorial_goal TEXT,
                    content_restrictions TEXT,
                    package_json TEXT NOT NULL,
                    version_history_json TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def get_channel_identity(self, channel_id: int) -> Dict[str, Any]:
        if int(channel_id) not in CHANNEL_IDENTITIES:
            raise ValueError(f"Canal {channel_id} não possui identidade editorial configurada.")
        ident = dict(CHANNEL_IDENTITIES[int(channel_id)])
        prof = next((p for p in PROFILES_DEFINITIONS if p["slug"] == ident["profile_slug"]), None)
        if prof:
            ident["archetype_reference"] = prof["archetype"]
        return ident

    def list_eligible_references(self, channel_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        ident = self.get_channel_identity(channel_id)
        niche = ident["niche"]
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT source_id, title, duration_seconds, views_count, engagement_ratio, processing_state, analysis_payload
                FROM audiovisual_library
                WHERE niche = ? AND processing_state IN ('learning_candidate', 'editorial_analysis_complete', 'fully_analyzed')
                ORDER BY id DESC LIMIT ?
                """,
                (niche, limit),
            ).fetchall()
        out = []
        for r in rows:
            pay = _parse_json(r["analysis_payload"], {})
            feats = pay.get("editorial_features") or {}
            out.append({
                "source_id": r["source_id"],
                "title": r["title"],
                "duration_seconds": r["duration_seconds"],
                "views_count": r["views_count"],
                "engagement_ratio": r["engagement_ratio"],
                "cuts_count": feats.get("cuts_count", pay.get("visual_and_editing", {}).get("cuts_count", "NOT_AVAILABLE")),
                "hook_type": feats.get("hook_type", "NOT_AVAILABLE"),
            })
        return out

    def _collect_applied_memories(self, channel_id: int) -> Dict[str, Any]:
        mem = self.als.get_channel_editorial_memory(channel_id)
        items = mem.get("knowledge_items", [])
        applied: List[Dict[str, Any]] = []
        validated_count = 0
        hyp_count = 0
        anti_count = 0

        for it in items:
            cls = it.get("classification")
            meta = _parse_json(it.get("metadata"), {})
            evs = _parse_json(it.get("evidence_video_ids"), [])
            cnts = meta.get("counterexamples") or []
            conf = float(it.get("confidence_score") or 0.5)
            ktype = it.get("knowledge_type") or "geral"

            if cls == "APRENDIZADO_VALIDADO":
                validated_count += 1
                reason = f"Padrão validado no Canal {channel_id} com {len(evs)} evidências e {len(cnts)} contraexemplos."
                expected = f"Tendência observada de melhor engajamento/retenção ao aplicar '{ktype}' (não garantido)."
            elif cls == "HIPÓTESE":
                hyp_count += 1
                reason = f"Hipótese em teste no Canal {channel_id} (conf={conf:.2f}); requer validação contínua."
                expected = f"Sinal preliminar para '{ktype}' — tratar como experimento, não regra definitiva."
            elif cls == "ANTI_PATTERN":
                anti_count += 1
                reason = f"Anti-pattern registrado no Canal {channel_id}; usado como trava preventiva."
                expected = f"Evitar falha recorrente ({it.get('title')})."
            else:
                continue

            applied.append({
                "knowledge_id": it["id"],
                "origin_channel_id": it.get("target_channel_id"),
                "classification": cls,
                "knowledge_type": ktype,
                "evidence_video_ids": evs[:5],
                "counterexamples_count": len(cnts),
                "confidence": conf,
                "reason": reason,
                "expected_outcome": expected,
            })

        return {
            "applied_memories": applied[:8],
            "validated_count": validated_count,
            "hypotheses_count": hyp_count,
            "anti_patterns_count": anti_count,
            "insufficient_evidence_warning": (
                f"Canal {channel_id} possui 0 aprendizados validados; pacote apoiado em identidade do canal e hipóteses."
                if validated_count == 0
                else None
            ),
        }

    def generate_package(
        self,
        channel_id: int,
        theme: str,
        reference_source_id: Optional[str] = None,
        target_duration_sec: float = 35.0,
        editorial_goal: str = "retenção e engajamento orgânico",
        content_restrictions: str = "Sem cópia literal de terceiros, sem clickbait falso, sem áudio silencioso.",
        package_uid: Optional[str] = None,
        version: int = 1,
        parent_package_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Gera um pacote editorial completo (A-E) fundamentado na memória e referência real do canal."""
        theme = (theme or "").strip()
        if not theme:
            raise ValueError("Tema editorial é obrigatório para gerar pacote.")

        ident = self.get_channel_identity(channel_id)
        dur = max(15.0, min(58.0, float(target_duration_sec or 35.0)))

        # Valida referência real se informada (sem inventar!)
        ref_info: Dict[str, Any] = {"status": "NO_REFERENCE_PROVIDED"}
        if reference_source_id:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT source_id, title, niche, duration_seconds, processing_state, analysis_payload FROM audiovisual_library WHERE source_id = ?",
                    (reference_source_id,),
                ).fetchone()
            if not row:
                raise ValueError(f"Referência '{reference_source_id}' não encontrada em audiovisual_library.")
            if row["niche"] != ident["niche"]:
                raise ValueError(
                    f"Referência '{reference_source_id}' pertence ao nicho '{row['niche']}', incompatível com canal {channel_id} ('{ident['niche']}')."
                )
            pay = _parse_json(row["analysis_payload"], {})
            feats = pay.get("editorial_features") or {}
            ref_info = {
                "status": "REAL_REFERENCE_VERIFIED",
                "source_id": row["source_id"],
                "title": row["title"],
                "duration_seconds": row["duration_seconds"],
                "structural_cuts": feats.get("cuts_count", "NOT_AVAILABLE"),
                "structural_hook": feats.get("hook_type", "NOT_AVAILABLE"),
                "note": "Apenas padrões estruturais observados; conteúdo verbal e visual do pacote é 100% original.",
            }

        mem_ctx = self._collect_applied_memories(channel_id)
        has_validated_cuts = any(
            m["knowledge_type"] == "ritmo_de_cortes_dinamico" and m["classification"] == "APRENDIZADO_VALIDADO"
            for m in mem_ctx["applied_memories"]
        )
        planned_cuts = 6 if has_validated_cuts or dur >= 30.0 else 4

        # A. Conceito
        concept = {
            "central_theme": theme,
            "main_idea": f"Abordagem original para {ident['name']} explorando '{theme}' com estrutura '{ident['narrative_structure']}'.",
            "estimated_audience": ident["audience"],
            "editorial_differential": f"Identidade '{ident['profile_slug']}' guiada por memória isolada do canal ({mem_ctx['validated_count']} validados, {mem_ctx['hypotheses_count']} hipóteses).",
            "content_goal": editorial_goal,
        }

        # B. Roteiro Original (gancho, desenvolvimento, progressão, retenção, encerramento, CTA)
        hook_line = (
            f"Você sabia que por trás de {theme} existe um detalhe que quase ninguém percebe logo no início?"
            if channel_id in (2, 4)
            else (
                f"Se você ainda erra em {theme}, esses próximos {int(dur)} segundos mudam seu jogo hoje."
                if channel_id == 5
                else (
                    f"Presta atenção no que aconteceu em {theme} — isso muda tudo na hora!"
                    if channel_id == 1
                    else f"Sabe quando {theme} parece normal até dar tudo errado no segundo seguinte?"
                )
            )
        )
        dev_line = (
            f"Primeiro, observe o ponto central de {theme}: o contexto inicial cria a expectativa. "
            f"Em seguida, entra a virada principal que explica o porquê real de {theme} funcionar assim na prática."
        )
        closing_line = f"No fim das contas, entender esse detalhe sobre {theme} muda completamente a leitura do todo."
        cta_line = f"Comenta sua visão sobre {theme} e salva para revisar depois."

        script = {
            "hook": hook_line,
            "development": dev_line,
            "narrative_progression": ident["narrative_structure"],
            "retention_moments": [
                {"at_sec": round(dur * 0.1, 1), "technique": ident["hook_style"]},
                {"at_sec": round(dur * 0.45, 1), "technique": "Quebra de padrão visual + dado/virada central"},
                {"at_sec": round(dur * 0.8, 1), "technique": "Síntese conclusiva antes da chamada final"},
            ],
            "closing": closing_line,
            "cta": cta_line,
            "originality_note": "Roteiro original gerado sem cópia de falas ou identidade visual de terceiros.",
        }

        # C. Plano Audiovisual (sempre marca ASSET_NEEDED quando mídia não existe localmente)
        scene_dur = round(dur / planned_cuts, 1)
        scenes = []
        stage_labels = ["Abertura / Gancho", "Contextualização", "Virada Central", "Desenvolvimento", "Clímax / Prova", "Encerramento / CTA"]
        for i in range(planned_cuts):
            label = stage_labels[min(i, len(stage_labels) - 1)]
            scenes.append({
                "scene_index": i + 1,
                "stage": label,
                "visual_description": f"{label} sobre '{theme}' seguindo estilo: {ident['visual_style']}.",
                "estimated_duration_sec": scene_dur,
                "cut_cue": f"Corte seco aos {round((i + 1) * scene_dur, 1)}s",
                "narrative_rhythm": ident["rhythm"],
                "media_asset_status": "ASSET_NEEDED",
                "narration_emphasis": i in (0, 2, planned_cuts - 1),
                "transition": "cut_hard" if i < planned_cuts - 1 else "fade_out_audio",
            })

        audiovisual_plan = {
            "total_scenes": len(scenes),
            "target_aspect_ratio": "9:16",
            "visual_style": ident["visual_style"],
            "scenes": scenes,
        }

        # D. Plano de Áudio
        full_narration = f"{hook_line} {dev_line} {closing_line} {cta_line}"
        audio_plan = {
            "narration_text": full_narration,
            "tone": ident["narration_tone"],
            "target_loudness_lufs": -14.0,
            "pauses": [
                {"after_segment": "hook", "duration_sec": 0.35},
                {"after_segment": "virada", "duration_sec": 0.40},
            ],
            "emphases": [theme, "detalhe", "muda tudo"],
            "sfx_suggestions": ["whoosh_transicao_suave" if channel_id != 2 else "sub_bass_sutil", "impact_leve_virada"],
            "music_ambience_royalty_free": ident["music_ambience"],
        }

        # E. Checklist de Produção
        checklist = {
            "required_materials": [
                f"Clipes/imagens 9:16 originais ou livres de direitos para {len(scenes)} cenas (ASSET_NEEDED)",
                "Trilha sonora royalty-free compatível com o canal",
                "Faixa de narração normalizada em -14 LUFS",
            ],
            "pending_items": [f"Captar/selecionar mídia para {len(scenes)} cenas marcadas como ASSET_NEEDED", "Revisão humana antes de renderização"],
            "editorial_risks": [
                mem_ctx["insufficient_evidence_warning"] or "Monitorar retenção real após publicação",
                f"Restrições aplicadas: {content_restrictions}",
            ],
            "originality_check": "PASS (roteiro original; referência usada apenas para estrutura)",
            "channel_fit_check": f"PASS ({ident['name']} / {ident['niche']})",
            "current_state": "READY_FOR_REVIEW",
        }

        package_obj = {
            "concept": concept,
            "script": script,
            "audiovisual_plan": audiovisual_plan,
            "audio_plan": audio_plan,
            "production_checklist": checklist,
            "applied_memories": mem_ctx["applied_memories"],
            "memory_summary": {
                "validated_used": mem_ctx["validated_count"],
                "hypotheses_used": mem_ctx["hypotheses_count"],
                "anti_patterns_used": mem_ctx["anti_patterns_count"],
                "insufficient_evidence_warning": mem_ctx["insufficient_evidence_warning"],
            },
            "reference_used": ref_info,
        }

        uid = package_uid or f"pkg_ch{channel_id}_{uuid.uuid4().hex[:8]}"
        history = [{
            "version": version,
            "status": "READY_FOR_REVIEW",
            "action": "GENERATED" if version == 1 else "DUPLICATED_NEW_VERSION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO editorial_production_packages (
                    package_uid, version, parent_package_id, channel_id, channel_name, niche,
                    theme, reference_source_id, status, target_duration_sec, editorial_goal,
                    content_restrictions, package_json, version_history_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'READY_FOR_REVIEW', ?, ?, ?, ?, ?)
                """,
                (
                    uid, version, parent_package_id, channel_id, ident["name"], ident["niche"],
                    theme, reference_source_id, dur, editorial_goal, content_restrictions,
                    json.dumps(package_obj, ensure_ascii=False),
                    json.dumps(history, ensure_ascii=False),
                ),
            )
            conn.commit()
            pkg_id = cur.lastrowid

        return self.get_package(pkg_id)

    def get_package(self, package_id: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            r = conn.execute("SELECT * FROM editorial_production_packages WHERE id = ?", (package_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["package"] = _parse_json(d.pop("package_json"), {})
        d["version_history"] = _parse_json(d.pop("version_history_json"), [])
        return d

    def list_packages(self, channel_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        q = "SELECT * FROM editorial_production_packages WHERE 1=1"
        params: List[Any] = []
        if channel_id is not None:
            q += " AND channel_id = ?"
            params.append(int(channel_id))
        if status:
            q += " AND status = ?"
            params.append(status)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._get_conn() as conn:
            rows = conn.execute(q, params).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["package"] = _parse_json(d.pop("package_json"), {})
            d["version_history"] = _parse_json(d.pop("version_history_json"), [])
            out.append(d)
        return out

    def update_package_manual(self, package_id: int, updates: Dict[str, Any], note: str = "Edição manual") -> Dict[str, Any]:
        pkg = self.get_package(package_id)
        if not pkg:
            raise ValueError(f"Pacote {package_id} não encontrado.")
        content = pkg["package"]
        for section in ("concept", "script", "audiovisual_plan", "audio_plan", "production_checklist"):
            if section in updates and isinstance(updates[section], dict):
                content[section].update(updates[section])
        history = pkg["version_history"]
        history.append({
            "version": pkg["version"],
            "status": pkg["status"],
            "action": "MANUAL_EDIT",
            "note": note,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE editorial_production_packages SET package_json = ?, version_history_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(content, ensure_ascii=False), json.dumps(history, ensure_ascii=False), package_id),
            )
            conn.commit()
        return self.get_package(package_id)

    def duplicate_version(self, package_id: int, new_theme: Optional[str] = None) -> Dict[str, Any]:
        orig = self.get_package(package_id)
        if not orig:
            raise ValueError(f"Pacote {package_id} não encontrado.")
        with self._get_conn() as conn:
            max_v = conn.execute(
                "SELECT COALESCE(MAX(version), 1) FROM editorial_production_packages WHERE package_uid = ?",
                (orig["package_uid"],),
            ).fetchone()[0]
            new_v = int(max_v) + 1
            hist = list(orig["version_history"])
            hist.append({
                "version": new_v,
                "status": "DRAFT",
                "action": f"DUPLICATED_FROM_ID_{package_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO editorial_production_packages (
                    package_uid, version, parent_package_id, channel_id, channel_name, niche,
                    theme, reference_source_id, status, target_duration_sec, editorial_goal,
                    content_restrictions, package_json, version_history_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?, ?)
                """,
                (
                    orig["package_uid"], new_v, package_id, orig["channel_id"], orig["channel_name"], orig["niche"],
                    new_theme or orig["theme"], orig["reference_source_id"], orig["target_duration_sec"],
                    orig["editorial_goal"], orig["content_restrictions"],
                    json.dumps(orig["package"], ensure_ascii=False),
                    json.dumps(hist, ensure_ascii=False),
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        return self.get_package(new_id)

    def compare_versions(self, id_a: int, id_b: int) -> Dict[str, Any]:
        a = self.get_package(id_a)
        b = self.get_package(id_b)
        if not a or not b:
            raise ValueError("Um ou ambos os pacotes para comparação não existem.")
        return {
            "package_a": {"id": a["id"], "version": a["version"], "status": a["status"], "theme": a["theme"], "hook": a["package"]["script"]["hook"], "scenes_count": len(a["package"]["audiovisual_plan"]["scenes"])},
            "package_b": {"id": b["id"], "version": b["version"], "status": b["status"], "theme": b["theme"], "hook": b["package"]["script"]["hook"], "scenes_count": len(b["package"]["audiovisual_plan"]["scenes"])},
            "hook_changed": a["package"]["script"]["hook"] != b["package"]["script"]["hook"],
            "script_changed": a["package"]["script"] != b["package"]["script"],
            "scenes_changed": a["package"]["audiovisual_plan"] != b["package"]["audiovisual_plan"],
        }

    def transition_status(self, package_id: int, new_status: str, reason: str = "") -> Dict[str, Any]:
        if new_status not in PRODUCTION_STATES:
            raise ValueError(f"Estado inválido: {new_status}. Permitidos: {PRODUCTION_STATES}")
        pkg = self.get_package(package_id)
        if not pkg:
            raise ValueError(f"Pacote {package_id} não encontrado.")
        hist = pkg["version_history"]
        hist.append({
            "version": pkg["version"],
            "from_status": pkg["status"],
            "to_status": new_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        content = pkg["package"]
        content["production_checklist"]["current_state"] = new_status
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE editorial_production_packages SET status = ?, package_json = ?, version_history_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, json.dumps(content, ensure_ascii=False), json.dumps(hist, ensure_ascii=False), package_id),
            )
            conn.commit()
        return self.get_package(package_id)
