"""
Módulo de Inteligência e Análise Profunda de Padrões Virais (Intelligence Engine).
Analisa abertura (0-3s), estrutura narrativa, ritmo de edição e cruza com métricas reais de engajamento.
"""
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from database.db import get_db_connection

class PatternAnalysisSchema(BaseModel):
    archetype: str = Field(description="Arquétipo: humor, treta_polemica, storytelling, curiosidade, educacional, esportes")
    hook_type: str = Field(description="Tipo de abertura: pergunta, afirmacao_chocante, quebra_de_expectativa, conflito_imediato")
    hook_duration_seconds: float = Field(description="Duração do gancho inicial em segundos (normalmente 2 a 4s)")
    hook_formula: str = Field(description="Fórmula psicológica usada na frase de abertura")
    narrative_structure: str = Field(description="Estrutura narrativa sequencial: ex: Pergunta inicial -> Exemplo extremo -> Reviravolta -> Conclusão")
    editing_pace: str = Field(description="Ritmo de edição observado: cortes rápidos a cada 2s, zooms enfáticos, legendas palavra por palavra")
    retention_elements: List[str] = Field(description="Lista de gatilhos psicológicos que mantêm a pessoa assistindo até o final")
    inferred_drop_points: str = Field(description="Possíveis pontos de abandono identificados (ex: transições lentas, explicações técnicas)")
    hypotheses_vs_facts: str = Field(description="Distinção clara entre o que é fato mensurável (views/likes) e o que é hipótese inferida")

class IntelligenceEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def analyze_reference_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Analisa a fundo um vídeo catalogado cruzando título, transcrição e métricas reais de engajamento.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.id, v.video_id, v.title, v.view_count, v.like_count, v.comment_count, 
                       v.engagement_rate, v.transcript_text, c.name as category_name, c.id as cat_id
                FROM video_references v
                LEFT JOIN categories c ON c.id = v.category_id
                WHERE v.video_id = ? OR v.id = ?
            """, (video_id, video_id))
            row = cursor.fetchone()

        if not row:
            print(f"[Intelligence] Vídeo não encontrado: {video_id}")
            return None

        title = row["title"]
        views = row["view_count"]
        likes = row["like_count"]
        comments = row["comment_count"]
        engagement = row["engagement_rate"]
        cat_name = row["category_name"]
        cat_id = row["cat_id"]

        print(f"[Intelligence] Analisando padrões do vídeo: '{title}' (Engajamento: {engagement}%)")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            prompt = f"""
            Você é um cientista de dados e estrategista sênior de retenção no YouTube Shorts.
            Analise rigorosamente esta referência de alto impacto e extraia o DNA do seu formato.
            
            DADOS REAIS DA PLATAFORMA:
            - Título: {title}
            - Categoria: {cat_name}
            - Visualizações reais: {views}
            - Curtidas: {likes}
            - Comentários: {comments}
            - Taxa de Engajamento Calculada: {engagement}%
            
            IMPORTANTE:
            - Distinga claramente dados reais (views/likes) de hipóteses inferidas.
            - Analise a abertura (0-3s), estrutura narrativa, ritmo de edição e os elementos de retenção.
            - Identifique a fórmula psicológica reproduzível para ser usada na geração de roteiros originais (sem plágio).
            """

            response = client.models.generate_content(
                model="gemini-4-hydrogen",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PatternAnalysisSchema,
                    temperature=0.2
                )
            )

            analysis: PatternAnalysisSchema = PatternAnalysisSchema.model_validate_json(response.text)

            # Salvar no banco de dados de Padrões
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO content_patterns (
                        category_id, archetype, hook_type, hook_duration_seconds,
                        hook_formula, narrative_structure, editing_pace,
                        retention_elements, performance_tier, sample_video_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cat_id,
                    analysis.archetype,
                    analysis.hook_type,
                    analysis.hook_duration_seconds,
                    analysis.hook_formula,
                    analysis.narrative_structure,
                    analysis.editing_pace,
                    json.dumps(analysis.retention_elements, ensure_ascii=False),
                    "top_tier" if engagement > 5.0 else "standard",
                    json.dumps([video_id])
                ))
                conn.commit()

            print(f"[Intelligence] Padrão extraído com sucesso! Arquétipo: {analysis.archetype} | Gancho: {analysis.hook_type}")
            return analysis.model_dump()

        except Exception as e:
            print(f"[Intelligence] Erro na análise com IA ({e})")
            return None

    def get_cross_category_insights(self) -> List[Dict[str, Any]]:
        """
        Cruza os padrões de todas as categorias cadastradas e gera relatórios de inteligência.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.archetype, p.hook_type, COUNT(p.id) as pattern_count,
                       c.name as category_name, p.hook_formula, p.narrative_structure
                FROM content_patterns p
                JOIN categories c ON c.id = p.category_id
                GROUP BY p.archetype, p.hook_type
                ORDER BY pattern_count DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
