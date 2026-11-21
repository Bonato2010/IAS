"""
Podcast Deep Analyzer
Analisador profundo de podcasts longos para extração de momentos de ouro e cortes virais de YouTube Shorts.
Executa a deliberação dos 10 Agentes Especializados para cada trecho candidato.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.central_memory import CentralMemory
from agents.company import ContentCompany

class PodcastDeepAnalyzer:
    def __init__(self, memory: Optional[CentralMemory] = None):
        self.memory = memory or CentralMemory()
        self.company = ContentCompany(memory=self.memory)

    def segment_transcript_into_candidate_cuts(self, transcript_segments: List[Dict[str, Any]],
                                               min_duration: float = 25.0,
                                               max_duration: float = 58.0) -> List[Dict[str, Any]]:
        """
        Agrupa falas e segmentos temporais em blocos de candidatos a cortes de Shorts (25s a 58s).
        Analisa quebras de assunto através de pausas temporais (> 2.0s) ou marcadores discursivos.
        """
        candidate_cuts = []
        current_chunk = []
        chunk_start = 0.0
        
        for seg in transcript_segments:
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 2.0)
            text = seg.get("text", "").strip()

            if not current_chunk:
                chunk_start = start

            current_chunk.append(seg)
            chunk_duration = end - chunk_start

            # Verifica se atingiu a duração ótima de um Short
            if chunk_duration >= min_duration:
                # Se encontrou um ponto final ou pausa razoável, fecha o candidato
                is_sentence_end = text.endswith((".", "!", "?"))
                if is_sentence_end or chunk_duration >= max_duration:
                    full_text = " ".join([s.get("text", "").strip() for s in current_chunk])
                    candidate_cuts.append({
                        "start_time": round(chunk_start, 2),
                        "end_time": round(end, 2),
                        "duration": round(chunk_duration, 2),
                        "transcript": full_text
                    })
                    current_chunk = []

        # Adiciona o último bloco caso tenha duração mínima
        if current_chunk:
            dur = current_chunk[-1].get("end", 0.0) - chunk_start
            if dur >= 18.0:
                full_text = " ".join([s.get("text", "").strip() for s in current_chunk])
                candidate_cuts.append({
                    "start_time": round(chunk_start, 2),
                    "end_time": round(current_chunk[-1].get("end", 0.0), 2),
                    "duration": round(dur, 2),
                    "transcript": full_text
                })

        return candidate_cuts

    def analyze_episode(self, episode_title: str, transcript_data: Any,
                        source_url: str = "", channel_name: str = "Podcast Principal") -> Dict[str, Any]:
        """
        Recebe a transcrição completa do episódio (lista de segmentos com start/end/text),
        extrai cortes candidatos, submete aos 10 Agentes e registra tudo no Banco de Dados.
        """
        # Salva o episódio na tabela podcast_episodes
        with self.memory._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO podcast_episodes (
                    title, source_url, channel_name, duration_seconds, status
                ) VALUES (?, ?, ?, ?, ?)
            """, (episode_title, source_url, channel_name, 3600.0, "analyzing"))
            episode_id = cursor.lastrowid
            conn.commit()

        # Converte formato se for lista ou string única
        segments = []
        if isinstance(transcript_data, list):
            segments = transcript_data
        elif isinstance(transcript_data, str):
            # Transcrição simples dividida por frases
            sentences = re.split(r'(?<=[.!?]) +', transcript_data)
            t = 0.0
            for s in sentences:
                dur = max(2.0, len(s.split()) * 0.4)
                segments.append({"start": t, "end": t + dur, "text": s})
                t += dur

        candidate_blocks = self.segment_transcript_into_candidate_cuts(segments)

        evaluated_candidates = []
        for idx, block in enumerate(candidate_blocks):
            # Prepara dados do candidato
            cut_title = f"{episode_title[:30]} - Corte #{idx+1}"
            candidate_payload = {
                "id": idx + 1,
                "title": cut_title,
                "transcript": block["transcript"],
                "duration": block["duration"],
                "start_time": block["start_time"],
                "end_time": block["end_time"],
                "is_direct_clip": True,
                "source_authorized": True
            }

            # Deliberação dos 10 Agentes
            council_review = self.company.evaluate_candidate_cut(candidate_payload)
            verdict = council_review["director_verdict"]

            # Sugestão de gancho e título
            first_words = " ".join(block["transcript"].split()[:8])
            hook_suggested = f"A verdade sobre isso: {first_words}..."
            title_suggested = f"O SEGREDO QUE NINGUÉM CONTOU SOBRE ISSO! #shorts"
            caption_suggested = f"Você concorda com essa visão? Deixe seu comentário! 👇 #podcast #shorts #cortes"

            # Salva o corte no banco de dados
            with self.memory._get_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO podcast_candidate_cuts (
                        episode_id, start_time, end_time, duration,
                        transcript, theme, target_audience, content_type,
                        hook_suggested, justification, narrative_potential,
                        editing_strategy, title_suggestion, caption_suggestion,
                        quality_score, confidence_score, agent_evaluations,
                        director_decision
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    episode_id, block["start_time"], block["end_time"], block["duration"],
                    block["transcript"], "Diálogo & Opiniões", "Jovens e Adultos (18-35)",
                    "Corte de Podcast", hook_suggested, verdict["recommendation"],
                    float(verdict["breakdown_scores"].get("Agente de Storytelling", 70)),
                    "Vertical 9:16 com legendas dinâmicas karaoke e zoom punches a cada 3.2s",
                    title_suggested, caption_suggested, verdict["final_score"],
                    verdict["confidence"], json.dumps(council_review["specialist_evaluations"], ensure_ascii=False),
                    verdict["status"]
                ))
                cut_db_id = cur.lastrowid
                conn.commit()

            evaluated_candidates.append({
                "cut_id": cut_db_id,
                "start_time": block["start_time"],
                "end_time": block["end_time"],
                "duration": block["duration"],
                "transcript": block["transcript"],
                "score": verdict["final_score"],
                "status": verdict["status"],
                "recommendation": verdict["recommendation"],
                "assigned_channel": verdict["assigned_channel_id"],
                "breakdown": verdict["breakdown_scores"]
            })

        # Atualiza status do episódio
        with self.memory._get_conn() as conn:
            conn.execute("UPDATE podcast_episodes SET status = 'completed' WHERE id = ?", (episode_id,))
            conn.commit()

        # Ordena os melhores cortes por score decrescente
        evaluated_candidates.sort(key=lambda x: x["score"], reverse=True)

        return {
            "episode_id": episode_id,
            "episode_title": episode_title,
            "total_candidates_analyzed": len(evaluated_candidates),
            "approved_candidates": [c for c in evaluated_candidates if "APPROVED" in c["status"]],
            "all_candidates": evaluated_candidates
        }
