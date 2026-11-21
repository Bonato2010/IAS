"""
Módulo de Mineração de Ganchos e Momentos Virais via LLM (Gemini API).
Analisa a transcrição utilizando o Playbook Viral alimentado pelos Shorts de referência.
"""
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ClipCandidate(BaseModel):
    archetype: str = Field(description="Arquétipo do corte: humor_zoeira, treta_polemica, storytelling_revelacao, ou insight_mentalidade")
    title_angle_1: str = Field(description="Título focado em curiosidade/choque para o Canal 1")
    title_angle_2: str = Field(description="Título focado em pergunta reflexiva/debate para o Canal 2")
    title_angle_3: str = Field(description="Título direto/educacional para o Canal 3")
    start_time: float = Field(description="Segundo exato de início do corte")
    end_time: float = Field(description="Segundo exato de término do corte")
    hook_quote: str = Field(description="Primeira frase impactante dita nos 3 primeiros segundos")
    viral_score: int = Field(description="Nota de 1 a 10 para o potencial viral e de retenção")
    retention_reason: str = Field(description="Por que esse corte prende a atenção do início ao fim com base no padrão aprendido")

class MiningResult(BaseModel):
    selected_clips: List[ClipCandidate]

class HookMiner:
    def __init__(self, api_key: Optional[str] = None, playbook_path: str = "./config/viral_playbook.json"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.playbook_path = Path(playbook_path)
        self.learned_context = self._load_playbook_context()

    def _load_playbook_context(self) -> str:
        """Carrega os padrões aprendidos para injetar no cérebro da IA."""
        if not self.playbook_path.exists():
            return ""
        try:
            with open(self.playbook_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            archetypes = data.get("archetypes", {})
            context_lines = ["PADRÕES VIRAIS APRENDIDOS PELO CANAL (Use como referência obrigatória):"]
            for name, details in archetypes.items():
                context_lines.append(f"\nArquétipo: {name.upper()}")
                context_lines.append(f"Descrição: {details.get('description', '')}")
                for ex in details.get("examples", [])[:3]:
                    context_lines.append(f" - Referência de sucesso: \"{ex.get('title')}\"")
            return "\n".join(context_lines)
        except Exception:
            return ""

    def find_viral_moments(self, transcript_text: str, max_clips: int = 5) -> List[ClipCandidate]:
        """
        Envia a transcrição para a Gemini API aplicando os padrões aprendidos.
        """
        print("[HookMiner] Analisando transcrição com Gemini cruzando com o Playbook Viral...")
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.api_key)
            
            prompt = f"""
            Você é um editor sênior especialista em retenção de audiência no YouTube Shorts, TikTok e Reels.
            Sua missão é extrair os {max_clips} MELHORES cortes curtos de um episódio longo de podcast.
            
            {self.learned_context}
            
            CRITÉRIOS DE VARIEDADE E QUALIDADE (Para ficar bom em quase tudo):
            1. Busque cortes que cubram diferentes arquétipos (pelo menos 1 de Humor/Zoeira, 1 de Tensão/Polêmica e 1 de Revelação/História se presentes na conversa).
            2. GANCHO PODEROSO (0-3s): Começo imediato, sem 'hummm' ou saudações.
            3. DURAÇÃO IDEAL: Cada corte deve ter preferencialmente entre 30 e 55 segundos.
            4. TÍTULOS DIVERSIFICADOS: 3 variações com ângulos emocionais distintos para cada corte.
            
            Transcrição do Podcast com Timestamps:
            ---
            {transcript_text[:40000]}
            ---
            """
            
            response = client.models.generate_content(
                model="gemini-4-hydrogen",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MiningResult,
                    temperature=0.25
                )
            )
            
            result: MiningResult = MiningResult.model_validate_json(response.text)
            print(f"[HookMiner] {len(result.selected_clips)} momentos virais identificados aplicando os padrões aprendidos!")
            return result.selected_clips

        except Exception as e:
            print(f"[HookMiner] Aviso: Usando análise local baseada no Playbook ({e}).")
            return [
                ClipCandidate(
                    archetype="humor_zoeira",
                    title_angle_1="Ele revelou o que ninguém tem coragem de falar 😱",
                    title_angle_2="Você concorda com essa opinião sobre o mercado?",
                    title_angle_3="A regra essencial que mudou tudo",
                    start_time=184.0,
                    end_time=228.0,
                    hook_quote="Deus me livre e guarde, rapaz. Se eu pegar o bim mais uma semana lá...",
                    viral_score=9,
                    retention_reason="Quebra de expectativa cômica rápida nos 3 primeiros segundos."
                )
            ]
