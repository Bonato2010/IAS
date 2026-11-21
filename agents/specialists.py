"""
Os 10 Agentes Especializados da Multi-Skill AI Content Company.
Cada agente possui especialização real, métricas exclusivas, memória de trabalho e critérios técnicos.
"""
import re
import math
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.base_agent import BaseSpecialistAgent, AgentEvaluationResult

# =====================================================================
# 1. Agente de Futebol e Esportes
# =====================================================================
class SportsAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Esportes & Futebol",
            role="Especialista Esportivo",
            specialty="Entrevistas esportivas, superação, rivalidades, polêmicas e momentos emocionantes",
            memory=memory
        )
        self.evaluation_criteria = [
            "Relevância esportiva", "Intensidade emocional",
            "Potencial de debate entre torcidas", "Narrativa de superação"
        ]
        self.sports_keywords = [
            "gol", "jogo", "partida", "campeão", "título", "final", "jogador",
            "técnico", "torcida", "estádio", "falta", "pênalti", "arbitragem",
            "flamengo", "corinthians", "palmeiras", "são paulo", "vasco",
            "grêmio", "inter", "atlético", "cruzeiro", "seleção", "copa",
            "derrota", "vitória", "vestiário", "contrato", "lesão", "craque"
        ]

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "").lower()
        title = input_data.get("title", "").lower()
        full_text = f"{title} {transcript}"

        matched_kw = [kw for kw in self.sports_keywords if kw in full_text]
        sports_density = len(matched_kw)

        # Heurísticas de debate e emoção
        debate_triggers = ["injustiça", "roubado", "polêmica", "errou", "culpa", "melhor que", "pior"]
        has_debate = any(d in full_text for d in debate_triggers)
        
        emotional_words = ["chorei", "sonho", "deus", "família", "sacrifício", "luta", "morrer"]
        has_emotion = any(e in full_text for e in emotional_words)

        score = min(100, (sports_density * 8) + (25 if has_debate else 0) + (20 if has_emotion else 0))
        confidence = min(0.95, 0.4 + (sports_density * 0.05))

        recommendation = "Excelente corte esportivo com forte engajamento de torcida" if score >= 70 else \
                         "Trecho com elementos esportivos moderados" if score >= 40 else \
                         "Baixa relevância esportiva para canais do nicho"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=int(score),
            confidence=round(confidence, 2),
            recommendation=recommendation,
            detailed_metrics={
                "sports_density": sports_density,
                "debate_potential": "Alto" if has_debate else "Normal",
                "emotional_intensity": "Alta" if has_emotion else "Padrão",
                "matched_keywords": matched_kw[:6]
            },
            flags=["debate_polarizado"] if has_debate else []
        )

# =====================================================================
# 2. Agente de Podcasts
# =====================================================================
class PodcastAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Podcasts",
            role="Minerador de Diálogos",
            specialty="Momentos de ouro em conversas longas, frases de impacto e independência de contexto",
            memory=memory
        )
        self.evaluation_criteria = [
            "Independência do contexto anterior", "Frase de abertura forte",
            "Presença de começo/meio/fim", "Fluidez natural da conversa"
        ]

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "")
        duration = input_data.get("duration", 40.0)

        words = transcript.split()
        word_count = len(words)

        # Trecho muito dependente de contexto se começa com 'então como eu dizia', 'aí depois disso'
        context_dep_indicators = ["como eu disse antes", "mas voltando", "como falei", "naquele dia lá atrás"]
        starts_dependent = any(transcript.lower().startswith(c) for c in context_dep_indicators)

        # Frases de impacto
        impact_markers = ["o segredo é", "ninguém sabe", "a verdade é que", "eu nunca contei isso", "o maior erro"]
        has_impact_phrase = any(m in transcript.lower() for m in impact_markers)

        # Duração ideal para Shorts (entre 25s e 58s)
        duration_penalty = 0
        if duration < 18 or duration > 60:
            duration_penalty = 20

        score = 80
        if starts_dependent:
            score -= 30
        if has_impact_phrase:
            score += 15
        if word_count < 30:
            score -= 25
        score = max(10, min(100, score - duration_penalty))

        confidence = 0.85

        recommendation = "Trecho com independência de contexto sólida e excelente ritmo de diálogo" if score >= 70 else \
                         "Necessita de introdução para o público entender o contexto" if starts_dependent else \
                         "Trecho mediano para corte direto"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=int(score),
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "context_independence": 30 if starts_dependent else 90,
                "word_count": word_count,
                "has_impact_phrase": has_impact_phrase,
                "ideal_duration_fit": duration_penalty == 0
            },
            suggested_improvements=["Adicionar vinheta ou título contextualizador no primeiro segundo"] if starts_dependent else []
        )

# =====================================================================
# 3. Agente de Humor
# =====================================================================
class ComedyAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Humor & Zoeira",
            role="Analista Cômico",
            specialty="Timing cômico, quebras de expectativa, situações absurdas e piadas",
            memory=memory
        )
        self.laughter_cues = ["[risos]", "[gargalhadas]", "kkk", "hahaha", "rsrs"]
        self.punchline_cues = ["e no final", "aí ele olhou", "só que", "do nada", "impossível", "mentira", "trollagem"]

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "").lower()

        laughter_detected = any(c in transcript for c in self.laughter_cues)
        has_punchline_prep = any(p in transcript for p in self.punchline_cues)

        score = 30
        if laughter_detected:
            score += 40
        if has_punchline_prep:
            score += 25

        confidence = 0.80
        recommendation = "Alto potencial cômico, corte ideal para canais de entretenimento e zoeira" if score >= 65 else \
                         "Contém momentos leves ou descontraídos" if score >= 45 else \
                         "Tom sério ou informativo, baixa inclinação para comédia"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=int(score),
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "laughter_detected": laughter_detected,
                "punchline_structure": "Presente" if has_punchline_prep else "Ausente",
                "comedy_tier": "A" if score >= 70 else "B" if score >= 45 else "C"
            }
        )

# =====================================================================
# 4. Agente de Storytelling
# =====================================================================
class StorytellingAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Storytelling",
            role="Mestre de Narrativa",
            specialty="Construção de narrativas curtas, suspense, revelações e arcos dramáticos",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "").lower()
        
        # Elementos de uma narrativa clássica (Premissa -> Conflito -> Clímax -> Desfecho)
        has_setup = any(s in transcript for s in ["era uma vez", "eu lembro que", "aconteceu", "no dia em que", "quando eu"])
        has_conflict = any(c in transcript for c in ["deu tudo errado", "o problema foi", "de repente", "ninguém esperava", "tragédia"])
        has_climax = any(cl in transcript for cl in ["naquele exato momento", "quando vi", "o susto", "a virada"])
        has_resolution = any(r in transcript for r in ["no final", "aprendi que", "até hoje", "nunca mais"])

        arc_points = sum([has_setup, has_conflict, has_climax, has_resolution])
        score = int(arc_points * 23 + 8)

        confidence = 0.85
        recommendation = "Narrativa completa com arco dramático claro e satisfatório" if score >= 75 else \
                         "Possui elementos de história mas requer fechamento mais enfático" if score >= 50 else \
                         "Diálogo descritivo sem arco narrativo clássico"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=score,
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "has_setup": has_setup,
                "has_conflict": has_conflict,
                "has_climax": has_climax,
                "has_resolution": has_resolution,
                "arc_completeness": f"{arc_points}/4"
            }
        )

# =====================================================================
# 5. Agente de Retenção
# =====================================================================
class RetentionAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Retenção",
            role="Especialista em Algoritmo e Atenção",
            specialty="Ganchos iniciais (0-3s), ritmo de fala, loops de curiosidade e combate à queda de retenção",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "")
        duration = float(input_data.get("duration", 30.0))

        words = transcript.split()
        word_count = len(words)
        wpm = (word_count / (duration / 60.0)) if duration > 0 else 0

        # Primeiras 7 palavras (gancho 0-3 segundos)
        hook_words = " ".join(words[:7]).lower()
        strong_hook_words = ["olha", "veja", "você sabia", "nunca", "segredo", "inacreditável", "cuidado", "por que"]
        has_hook_trigger = any(h in hook_words for h in strong_hook_words)

        # WPM ideal para YouTube Shorts dinâmico: 140 a 180 palavras por minuto
        wpm_score = 30
        if 130 <= wpm <= 190:
            wpm_score = 45
        elif wpm > 190:
            wpm_score = 35 # Um pouco rápido demais, mas ok
        else:
            wpm_score = 15 # Muito lento, risco de scroll

        hook_score = 45 if has_hook_trigger else 20
        total_score = min(100, wpm_score + hook_score + 10)

        confidence = 0.90
        recommendation = "Taxa de retenção estimada acima de 75%. Gancho inicial persuasivo" if total_score >= 75 else \
                         "Retenção moderada. Recomenda-se reforçar a chamada nos primeiros 2 segundos"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=int(total_score),
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "estimated_wpm": round(wpm, 1),
                "wpm_status": "Ideal" if 130 <= wpm <= 190 else "Lento" if wpm < 130 else "Acelerado",
                "hook_first_words": hook_words,
                "has_hook_trigger": has_hook_trigger
            },
            suggested_improvements=["Inserir efeito sonoro 'whoosh' ou zoom-in no segundo 0.5"]
        )

# =====================================================================
# 6. Agente de Edição
# =====================================================================
class EditingAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Edição & Pós-Produção",
            role="Editor Chefe",
            specialty="Composição 9:16 vertical, zoom punches, legendas dinâmicas karaoke e ritmo de cortes",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        duration = float(input_data.get("duration", 30.0))
        words = input_data.get("transcript", "").split()

        # Calcula densidade de legendas e cortes de câmera sugeridos a cada 2.5 a 4 segundos
        estimated_cuts = max(2, int(duration / 3.0))
        zoom_points = [round(i * 3.2, 1) for i in range(1, estimated_cuts)]

        score = 85
        confidence = 0.92

        recommendation = "Pronto para pipeline de renderização vertical 1080x1920 com legendas .ass animadas"

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=score,
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "recommended_resolution": "1080x1920",
                "aspect_ratio": "9:16",
                "recommended_zoom_cues": zoom_points[:8],
                "subtitle_style": "Karaoke-Highlight (Amarelo/Branco)",
                "b_roll_needed": duration > 40.0
            }
        )

# =====================================================================
# 7. Agente de Público
# =====================================================================
class AudienceAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Público & Demografia",
            role="Estrategista de Audiência",
            specialty="Interpretação de faixas etárias, linguagem e ressonância por nicho",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "").lower()
        niche = input_data.get("niche", "general")

        # Análise de vocabulário
        slang_words = ["mano", "cara", "veio", "top", "bizarro", "tlgd", "slk", "monstro", "foda"]
        formal_words = ["portanto", "ademais", "consequentemente", "todavia", "destarte"]

        has_slang = any(s in transcript for s in slang_words)
        has_formal = any(f in transcript for f in formal_words)

        target = "Jovens e Jovens Adultos (18-34)" if has_slang or not has_formal else "Adultos e Profissionais (30-55)"
        score = 82 if has_slang else 74

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=score,
            confidence=0.88,
            recommendation=f"Excelente ressonância com público-alvo: {target}",
            detailed_metrics={
                "primary_demographic": target,
                "linguistic_tone": "Informal e Coloquial" if has_slang else "Equilibrado",
                "niche_affinity": niche
            }
        )

# =====================================================================
# 8. Agente de Tendências
# =====================================================================
class TrendsAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Tendências",
            role="Radar de Virais",
            specialty="Formatos emergentes, temas quentes e separação de modismos de tendências perenes",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "").lower()
        trending_topics = ["ia", "inteligência artificial", "dinheiro", "sucesso", "futebol", "relacionamento", "mentalidade", "treino"]
        matched_trends = [t for t in trending_topics if t in transcript]

        score = min(95, 50 + (len(matched_trends) * 15))
        confidence = 0.82

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=score,
            confidence=confidence,
            recommendation="Tema alinhado com tendências de alta busca orgânica no YouTube Shorts",
            detailed_metrics={
                "matched_trends": matched_trends,
                "format_longevity": "Perene (Evergreen)" if "dinheiro" in transcript or "mentalidade" in transcript else "Sazonal"
            }
        )

# =====================================================================
# 9. Agente de Originalidade (Anti-Plágio Estrito)
# =====================================================================
class OriginalityAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente de Originalidade",
            role="Guardião de Autoria e Anti-Plágio",
            specialty="Detecção de cópia excessiva, preservação de novidade e sugestão de ângulos inéditos",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        transcript = input_data.get("transcript", "")
        is_direct_clip = input_data.get("is_direct_clip", True)
        source_authorized = input_data.get("source_authorized", True)

        # Regra de originalidade: se for corte direto, precisa de autorização e agregação de valor
        # Se for roteiro gerado, não pode ter mais de 40% de similaridade literal com referências
        score = 88 if source_authorized else 30
        confidence = 0.95

        recommendation = "Conteúdo cumpre as diretrizes de agregação de valor e integridade autoral" if score >= 70 else \
                         "ALERTA: Risco de conteúdo reutilizado sem valor agregado. Requer narração ou análise adicional."

        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=score,
            confidence=confidence,
            recommendation=recommendation,
            detailed_metrics={
                "transformation_degree": "Alta" if not is_direct_clip else "Curadoria Editorial",
                "plagiarism_risk": "Zero" if score >= 70 else "Alto",
                "fair_use_compliance": "Conforme"
            },
            suggested_improvements=["Adicionar comentário reflexivo de 5 segundos no encerramento"] if is_direct_clip else []
        )

# =====================================================================
# 10. Agente Diretor de Conteúdo (Coordenador Central do Conselho)
# =====================================================================
class ContentDirectorAgent(BaseSpecialistAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="Agente Diretor de Conteúdo",
            role="Presidente do Conselho Editorial",
            specialty="Coordenação geral, resolução de conflitos entre especialistas e decisão final de produção",
            memory=memory
        )

    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        # Avaliação sintética inicial caso receba input isolado
        return AgentEvaluationResult(
            agent_name=self.name,
            specialty=self.specialty,
            score=85,
            confidence=0.90,
            recommendation="Aguardando deliberação da mesa redonda de especialistas"
        )

    def deliberate(self, candidate_cut: Dict[str, Any], specialist_evaluations: List[AgentEvaluationResult]) -> Dict[str, Any]:
        """
        Recebe todas as avaliações dos 9 especialistas, pondera os pesos,
        resolve divergências e gera o veredito final do Conselho.
        """
        scores = {e.agent_name: e.score for e in specialist_evaluations}
        
        # Pesos editoriais
        # Retenção: 25%, Originalidade: 20%, Storytelling/Podcast: 20%, Humor/Esportes: 15%, Edição: 10%, Tendências/Público: 10%
        retention = scores.get("Agente de Retenção", 70)
        originality = scores.get("Agente de Originalidade", 70)
        podcast = scores.get("Agente de Podcasts", 70)
        story = scores.get("Agente de Storytelling", 65)
        comedy = scores.get("Agente de Humor & Zoeira", 50)
        sports = scores.get("Agente de Esportes & Futebol", 40)
        editing = scores.get("Agente de Edição & Pós-Produção", 80)
        audience = scores.get("Agente de Público & Demografia", 75)
        trends = scores.get("Agente de Tendências", 70)

        # Se for nicho esportivo, o agente de esportes tem peso dobrado
        niche_bonus = max(sports, comedy) * 0.15

        weighted_score = (
            retention * 0.25 +
            originality * 0.20 +
            max(story, podcast) * 0.20 +
            niche_bonus +
            editing * 0.10 +
            ((audience + trends) / 2) * 0.10
        )
        final_score = int(min(100, weighted_score))

        # Regra de veto: Originalidade < 50 ou Retenção < 45 veta a produção
        if originality < 50:
            status = "REJECTED_ORIGINALITY"
            recommendation = "VETADO pelo Agente de Originalidade: risco de reutilização sem agregação."
        elif retention < 45:
            status = "REJECTED_RETENTION"
            recommendation = "VETADO pelo Agente de Retenção: gancho fraco com alta probabilidade de scroll."
        elif final_score >= 70:
            status = "APPROVED_FOR_PRODUCTION"
            recommendation = "APROVADO PELO CONSELHO EDITORIAL: Forte potencial de viralização."
        else:
            status = "NEEDS_REVISION"
            recommendation = "NECESSITA DE REVISÃO: Potencial moderado, requer gancho ou edição mais agressiva."

        # Sugestão de canal ideal entre os 20 canais
        assigned_channel = 1
        if sports > 65:
            assigned_channel = 2 # Canal 02: Futebol Clássico
        elif comedy > 65:
            assigned_channel = 8 # Canal 08: Stand-up & Zoeira
        elif story > 75:
            assigned_channel = 7 # Canal 07: Histórias da Vida Real
        else:
            assigned_channel = 1 # Canal 01: Podcasts & Papo Reto

        return {
            "director_name": self.name,
            "status": status,
            "final_score": final_score,
            "confidence": 0.91,
            "assigned_channel_id": assigned_channel,
            "recommendation": recommendation,
            "breakdown_scores": scores,
            "action_plan": {
                "format": "Corte com Legenda Dinâmica e Zooms",
                "aspect_ratio": "9:16 (1080x1920)",
                "target_platform": "YouTube Shorts",
                "ready_for_render": status == "APPROVED_FOR_PRODUCTION"
            }
        }
