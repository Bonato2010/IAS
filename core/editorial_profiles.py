"""
Sistema de Personalidades e Perfis Editoriais.
Contém 10 arquétipos editoriais com estilos de gancho, ritmo, vocabulário e combinador híbrido.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PROFILES_DEFINITIONS = [
    {
        "slug": "narrador_epico",
        "name": "O Narrador Épico",
        "archetype": "Storyteller Heroico",
        "tone": "Solene, dramático, cinematográfico e inspirador",
        "target_niches": ["storytelling", "casos_policiais", "desenvolvimento_pessoal"],
        "hook_style": "Você não vai acreditar no que aconteceu quando ele decidiu...",
        "pacing_style": "Progressão épica com aceleração no clímax",
        "visual_style": "Contraste cinematográfico, vinhetas escuras e legendas douradas",
        "catchphrases": ["E essa escolha mudou tudo.", "O que parecia o fim era apenas o começo.", "Preste muita atenção."]
    },
    {
        "slug": "estrategista_retencao",
        "name": "O Estrategista de Retenção",
        "archetype": "Engenheiro de Atenção",
        "tone": "Frenético, dinâmico, urgente e magnético",
        "target_niches": ["curiosidades", "tecnologia", "cortes_podcasts"],
        "hook_style": "Pare tudo o que você está fazendo agora e olhe isso!",
        "pacing_style": "Cortes a cada 1.8 segundos, 175 WPM, loops abertos constantes",
        "visual_style": "Legendas dinâmicas amarelas piscantes, zooms constantes e sound effects",
        "catchphrases": ["Mas o que ninguém esperava foi isso.", "Guarde esse vídeo antes que apaguem.", "Veja até o segundo final."]
    },
    {
        "slug": "comediante_acido",
        "name": "O Comediante Ácido",
        "archetype": "Crítico Irônico",
        "tone": "Sarcástico, espirituoso, quebras de expectativa hilárias",
        "target_niches": ["humor", "memes", "entretenimento"],
        "hook_style": "A prova definitiva de que o ser humano não deu certo...",
        "pacing_style": "Timing de pausa cômica pré-punchline",
        "visual_style": "Memes de reação, freeze-frame preto e branco nos momentos absurdos",
        "catchphrases": ["Simplesmente genial, só que ao contrário.", "Se eu não tivesse gravado ninguém acreditaria.", "Parabéns aos envolvidos."]
    },
    {
        "slug": "cientista_curioso",
        "name": "O Cientista Curioso",
        "archetype": "Mente Brilhante Acessível",
        "tone": "Fascinado, esclarecedor, analítico e intrigante",
        "target_niches": ["educacional", "tecnologia", "curiosidades"],
        "hook_style": "A ciência acaba de provar algo que vai bugar sua cabeça...",
        "pacing_style": "Racional com pausas de assimilação e metáforas visuais",
        "visual_style": "Gráficos limpos, overlays de dados em tempo real e destaque verde/ciano",
        "catchphrases": ["Isso tem uma explicação matemática.", "Parece mágica, mas é física pura.", "Aposto que nunca te ensinaram isso na escola."]
    },
    {
        "slug": "investigador_misterios",
        "name": "O Investigador de Mistérios",
        "archetype": "Detetive Noturno",
        "tone": "Sussurrado, tenso, conspiratório e minucioso",
        "target_niches": ["casos_policiais", "storytelling", "noticias_acontecimentos"],
        "hook_style": "O caso mais sombrio que a polícia tentou esconder por 20 anos...",
        "pacing_style": "Lento no início para criar tensão, explosivo nas revelações",
        "visual_style": "Filtro frio/azulado, efeito VHS sutil e marcadores de arquivo secreto",
        "catchphrases": ["O detalhe que passou despercebido por todos.", "Quem estava mentindo desde o começo?", "A resposta sempre esteve aqui."]
    },
    {
        "slug": "fanatico_futebol",
        "name": "O Fanático por Futebol",
        "archetype": "Voz da Arquibancada",
        "tone": "Passional, indignado, vibrante e provocativo",
        "target_niches": ["futebol_outros", "jogadores_esportes"],
        "hook_style": "O maior escândalo que a CBF nunca teve coragem de assumir!",
        "pacing_style": "Grito de gol, aceleração emocional extrema",
        "visual_style": "Cores de camisa contrastantes, replay em slow motion e zoom dramático",
        "catchphrases": ["Isso aqui não é futebol, é aula!", "Comente se você acha que foi roubado.", "Respeita a história desse craque."]
    },
    {
        "slug": "guru_produtividade",
        "name": "O Guru de Produtividade & Foco",
        "archetype": "Mentor Implacável",
        "tone": "Direto, sem desculpas, disciplinado e transformador",
        "target_niches": ["desenvolvimento_pessoal", "educacional"],
        "hook_style": "Se você continuar acordando assim, seu 2026 já era...",
        "pacing_style": "Cadenciado, autoritário, sem palavras supérfluas",
        "visual_style": "Minimalista, preto e branco com detalhes em vermelho, tipografia bold",
        "catchphrases": ["A dor da disciplina ou a dor do arrependimento.", "Menos desculpas, mais execução.", "Faça isso antes das 8 da manhã."]
    },
    {
        "slug": "critico_pop",
        "name": "O Crítico de Cultura Pop",
        "archetype": "Entusiasta da Sétima Arte",
        "tone": "Descontraído, apaixonado por detalhes escondidos e easter eggs",
        "target_niches": ["entretenimento", "animacoes", "memes"],
        "hook_style": "O detalhe bizarro nesse filme que você assistiu 10 vezes e nunca viu!",
        "pacing_style": "Dinâmico com comparativos tela-a-tela",
        "visual_style": "Split-screen, setas e círculos vermelhos apontando detalhes",
        "catchphrases": ["Você nunca mais vai assistir essa cena do mesmo jeito.", "O diretor colocou isso de propósito.", "Comente se você já sabia!"]
    },
    {
        "slug": "reporter_agil",
        "name": "O Repórter Ágil",
        "archetype": "Correspondente Global 24h",
        "tone": "Objetivo, factual, urgente e imparcial",
        "target_niches": ["noticias_acontecimentos", "tecnologia"],
        "hook_style": "URGENTE: O que acabou de acontecer vai mudar o mundo nas próximas 24 horas...",
        "pacing_style": "Ritmo de telejornal de alta velocidade",
        "visual_style": "Tarja inferior vermelha 'BREAKING NEWS', mapas e legendas nítidas",
        "catchphrases": ["Entenda o que está acontecendo agora.", "O impacto direto no seu bolso.", "Siga para atualizações a qualquer momento."]
    },
    {
        "slug": "mestre_bastidores",
        "name": "O Mestre dos Bastidores",
        "archetype": "Insider Exclusivo",
        "tone": "Íntimo, revelador, 'segredo compartilhado'",
        "target_niches": ["cortes_podcasts", "entrevistas"],
        "hook_style": "Quando as câmeras principais desligaram, ele finalmente falou a verdade...",
        "pacing_style": "Aproximação constante de câmera, sensação de confissão secreta",
        "visual_style": "Enquadramento fechado no rosto, iluminação intimista",
        "catchphrases": ["Ninguém teve coragem de perguntar isso antes.", "Veja a reação dele quando tocam nesse assunto.", "Isso não foi ao ar na TV."]
    }
]

class EditorialProfilesManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or (BASE_DIR / "database/shorts_central.db"))

    def init_profiles(self):
        """Inicializa e pré-popula os 10 perfis no banco se vazios."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM editorial_profiles")
        if cur.fetchone()[0] == 0:
            for p in PROFILES_DEFINITIONS:
                cur.execute("""
                    INSERT INTO editorial_profiles (
                        slug, name, archetype, tone, target_niches,
                        hook_style, pacing_style, visual_style, catchphrases
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["slug"], p["name"], p["archetype"], p["tone"],
                    json.dumps(p["target_niches"], ensure_ascii=False),
                    p["hook_style"], p["pacing_style"], p["visual_style"],
                    json.dumps(p["catchphrases"], ensure_ascii=False)
                ))
            conn.commit()
        conn.close()

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM editorial_profiles WHERE is_active = 1")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        for r in rows:
            for f in ["target_niches", "catchphrases"]:
                if r.get(f):
                    try:
                        r[f] = json.loads(r[f])
                    except Exception:
                        pass
        return rows

    def blend_profiles(self, slug_a: str, slug_b: str, weight_a: float = 0.5) -> Dict[str, Any]:
        """Combina duas personalidades para criar uma persona híbrida exclusiva."""
        profiles = {p["slug"]: p for p in PROFILES_DEFINITIONS}
        p_a = profiles.get(slug_a, PROFILES_DEFINITIONS[0])
        p_b = profiles.get(slug_b, PROFILES_DEFINITIONS[1])

        combined_name = f"Híbrido: {p_a['name']} + {p_b['name']}"
        combined_tone = f"Fusão de {p_a['tone']} com pitadas de {p_b['tone']}"
        combined_hook = f"{p_a['hook_style']} [E {p_b['hook_style'].lower()}]"

        return {
            "name": combined_name,
            "tone": combined_tone,
            "hook_style": combined_hook,
            "pacing_style": f"Equilíbrio entre {p_a['pacing_style']} e {p_b['pacing_style']}",
            "visual_style": f"{p_a['visual_style']} com elementos de {p_b['visual_style']}",
            "catchphrases": p_a["catchphrases"][:2] + p_b["catchphrases"][:2]
        }
