"""
Módulo de Geração Inteligente de Ideias e Roteiros 100% Originais.
Aprende com a estrutura dos padrões virais, sem copiar falas nem cometer plágio.
"""
import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from database.db import get_db_connection

class GeneratedScriptSchema(BaseModel):
    title: str = Field(description="Título de altíssima taxa de clique (CTR) respeitando o nicho")
    archetype: str = Field(description="Arquétipo aplicado (ex: curiosidade, humor, storytelling, polemica)")
    hook_3s: str = Field(description="Primeira frase exata dita nos 3 primeiros segundos (Gancho mortal)")
    full_script: str = Field(description="Roteiro de locução completo e original (120 a 160 palavras, aprox 45-55s)")
    visual_cues: str = Field(description="Indicações de cortes, B-rolls, zooms e elementos gráficos em cena")
    audio_cues: str = Field(description="Efeitos sonoros (whoosh, pop, batida) e estilo de trilha de fundo")
    recommended_duration: float = Field(description="Duração estimada em segundos (ex: 45.0)")
    editing_style: str = Field(description="Estilo de edição recomendado para o nicho do canal")

class ScriptGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate_original_script(
        self,
        channel_id: int,
        topic: str,
        target_archetype: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Gera um roteiro 100% original customizado para o nicho e tom de comunicação do canal.
        """
        # 1. Carregar perfil do canal
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels WHERE id = ? OR channel_number = ?", (channel_id, channel_id))
            channel = cursor.fetchone()

        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado.")

        ch_name = channel["name"]
        ch_niche = channel["niche"]
        ch_tone = channel["communication_tone"]
        ch_style = channel["editing_style"]
        ch_audience = channel["target_audience"]

        # 2. Carregar padrões de sucesso associados ao nicho
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hook_type, hook_formula, narrative_structure, retention_elements
                FROM content_patterns
                ORDER BY id DESC LIMIT 3
            """)
            patterns = cursor.fetchall()

        patterns_context = ""
        for p in patterns:
            patterns_context += f"- Fórmula de Gancho: {p['hook_formula']} | Estrutura: {p['narrative_structure']}\n"

        print(f"[ScriptGen] Gerando roteiro original para '{ch_name}' sobre tema: '{topic}'...")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            prompt = f"""
            Você é o roteirista-chefe de uma rede de canais de Shorts de alto nível.
            Crie um ROTEIRO 100% ORIGINAL para YouTube Shorts sobre o tema solicitado.
            
            PERFIL DO CANAL:
            - Nome: {ch_name}
            - Nicho: {ch_niche}
            - Tom de Comunicação: {ch_tone}
            - Estilo de Edição: {ch_style}
            - Público-Alvo: {ch_audience}
            
            TEMA DO VÍDEO: {topic}
            ARQUÉTIPO DESEJADO: {target_archetype or 'Curiosidade / Storytelling'}
            
            ESTRUTURAS NARRATIVAS DE SUCESSO IDENTIFICADAS NO BANCO:
            {patterns_context}
            
            REGRAS INEGOCIÁVEIS:
            1. ZERO PLÁGIO: O texto deve ser inteiramente original e criativo, aprendendo apenas com as estruturas de retenção.
            2. GANCHO (0-3s): Comece imediatamente sem saudações (ex: "Você sabia...", "Isso quase acabou com...", "A regra que ninguém te conta...").
            3. DURAÇÃO: 40 a 55 segundos de fala fluida e dinâmica (120 a 160 palavras).
            4. Chamada de ação final orgânica (CTA) para engajar nos comentários.
            """

            response = client.models.generate_content(
                model="gemini-4-hydrogen",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedScriptSchema,
                    temperature=0.3
                )
            )

            script: GeneratedScriptSchema = GeneratedScriptSchema.model_validate_json(response.text)

            # Salvar no banco de dados de roteiros
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scripts (
                        channel_id, title, archetype, hook_3s, full_script,
                        visual_cues, audio_cues, recommended_duration, editing_style,
                        status, human_approved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'idea', 0)
                """, (
                    channel["id"],
                    script.title,
                    script.archetype,
                    script.hook_3s,
                    script.full_script,
                    script.visual_cues,
                    script.audio_cues,
                    script.recommended_duration,
                    script.editing_style
                ))
                script_id = cursor.lastrowid
                conn.commit()

            print(f"[ScriptGen] Roteiro #{script_id} gerado com sucesso: '{script.title}'")
            res_dict = script.model_dump()
            res_dict["id"] = script_id
            return res_dict

        except Exception as e:
            print(f"[ScriptGen] Erro na geração com IA ({e})")
            return None

    def approve_script(self, script_id: int, approved: bool = True, notes: str = "") -> bool:
        """Aprovação humana mandatória antes de avançar para a produção."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            status = "approved" if approved else "rejected"
            cursor.execute("""
                UPDATE scripts SET
                    human_approved = ?,
                    status = ?,
                    approval_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (1 if approved else 0, status, notes, script_id))
            conn.commit()
            return cursor.rowcount > 0
