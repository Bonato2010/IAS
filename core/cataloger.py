"""
Módulo de Pesquisa e Catalogação em Massa de Shorts de Referência (2.000 a 3.000 Vídeos).
Respeita direitos autorais: cataloga metadados, métricas e análises sem baixar arquivos não autorizados.
"""
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from database.db import get_db_connection

class ReferenceCataloger:
    # Termos de busca estratégicos para cada categoria inicial
    CATEGORY_SEARCH_QUERIES = {
        "cortes_podcasts": ["cortes podcast shorts", "podcast momentos virais shorts", "entrevista polemica shorts"],
        "jogadores_esportes": ["lances lendarios futebol shorts", "melhores jogadas basquete shorts", "analise tatica shorts"],
        "futebol_outros": ["futebol habilidade shorts", "gols inacreditaveis shorts", "esportes radicais momentos shorts"],
        "humor": ["comedia standup shorts", "zoeira humor brasil shorts", "trollagem engracada shorts"],
        "memes": ["memes virais brasil shorts", "trend tik tok meme shorts", "shitpost de qualidade shorts"],
        "storytelling": ["historias reais bizarras shorts", "o dia que tudo mudou shorts", "relatos emocionantes shorts"],
        "animacoes": ["mini animacao shorts", "historias animadas shorts", "animacao 3d viral shorts"],
        "curiosidades": ["fatos que voce nao sabia shorts", "curiosidades do mundo shorts", "ciencia surpreendente shorts"],
        "noticias_acontecimentos": ["noticias urgentes shorts", "acontecimentos do mundo shorts", "fatos historicos shorts"],
        "casos_policiais": ["casos criminais reais shorts", "misterios nao resolvidos shorts", "investigacao criminal shorts"],
        "desenvolvimento_pessoal": ["mentalidade disciplina shorts", "dicas de produtividade shorts", "habitos de sucesso shorts"],
        "tecnologia": ["novidades tecnologia shorts", "inteligencia artificial ferramentas shorts", "gadgets incriveis shorts"],
        "educacional": ["aprenda em 1 minuto shorts", "dicas de estudo shorts", "explicando conceitos shorts"],
        "entretenimento": ["bastidores filmes famosos shorts", "curiosidades cinema shorts", "famosos declaracoes shorts"]
    }

    def __init__(self):
        pass

    def catalog_single_url(
        self,
        url: str,
        category_slug: str = "cortes_podcasts",
        subcategory: Optional[str] = None,
        permission: str = "reference_only"
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai metadados completos de um vídeo/short e salva no banco de dados.
        """
        print(f"[Cataloger] Catalogando metadados: {url}")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json",
            "--skip-download",
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[Cataloger] Erro ao extrair vídeo ({res.stderr[:80]})")
            return None

        try:
            info = json.loads(res.stdout)
            video_id = info.get("id") or url.split("v=")[-1].split("/")[-1]
            title = info.get("title", "Sem título")
            channel_title = info.get("uploader") or info.get("channel", "Desconhecido")
            channel_id = info.get("channel_id", "")
            duration = info.get("duration", 0)
            view_count = info.get("view_count", 0) or 0
            like_count = info.get("like_count", 0) or 0
            comment_count = info.get("comment_count", 0) or 0
            
            # Cálculo da taxa de engajamento
            engagement_rate = round(((like_count + comment_count) / view_count * 100), 2) if view_count > 0 else 0.0

            # Data de publicação
            upload_date_str = info.get("upload_date")
            pub_date = None
            if upload_date_str:
                try:
                    pub_date = datetime.strptime(upload_date_str, "%Y%m%d").isoformat()
                except Exception:
                    pub_date = None

            format_features = json.dumps({
                "width": info.get("width"),
                "height": info.get("height"),
                "fps": info.get("fps"),
                "aspect_ratio": "9:16" if (info.get("height", 0) > info.get("width", 1)) else "16:9",
                "vcodec": info.get("vcodec"),
                "tags": info.get("tags", [])[:10]
            }, ensure_ascii=False)

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,))
                row = cursor.fetchone()
                category_id = row[0] if row else 1

                cursor.execute("""
                    INSERT INTO video_references (
                        video_id, title, original_url, channel_title, channel_id,
                        category_id, subcategory, duration_seconds, published_at,
                        view_count, like_count, comment_count, engagement_rate,
                        format_features, usage_permission, availability_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    ON CONFLICT(video_id) DO UPDATE SET
                        view_count = excluded.view_count,
                        like_count = excluded.like_count,
                        comment_count = excluded.comment_count,
                        engagement_rate = excluded.engagement_rate
                """, (
                    video_id, title, url, channel_title, channel_id,
                    category_id, subcategory or category_slug, duration, pub_date,
                    view_count, like_count, comment_count, engagement_rate,
                    format_features, permission
                ))
                conn.commit()

            print(f"[Cataloger] Vídeo salvo: '{title[:45]}...' | Views: {view_count} | Engajamento: {engagement_rate}%")
            return {
                "video_id": video_id,
                "title": title,
                "views": view_count,
                "engagement_rate": engagement_rate
            }
        except Exception as e:
            print(f"[Cataloger] Falha ao processar JSON ({e})")
            return None

    def batch_catalog_by_category(self, category_slug: str, limit: int = 50) -> int:
        """
        Pesquisa e cataloga em lote vídeos de referência de uma categoria específica.
        """
        queries = self.CATEGORY_SEARCH_QUERIES.get(category_slug, [f"{category_slug} shorts"])
        total_cataloged = 0

        for query in queries:
            print(f"[Cataloger] Buscando referências para: '{query}' (Meta: {limit})...")
            search_cmd = [
                sys.executable, "-m", "yt_dlp",
                f"ytsearch{limit}:{query}",
                "--dump-json",
                "--flat-playlist",
                "--skip-download"
            ]
            res = subprocess.run(search_cmd, capture_output=True, text=True)
            if res.returncode != 0:
                continue

            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    url = item.get("url") or f"https://www.youtube.com/watch?v={item.get('id')}"
                    # Cataloga o vídeo
                    saved = self.catalog_single_url(url, category_slug=category_slug)
                    if saved:
                        total_cataloged += 1
                        if total_cataloged >= limit:
                            break
                except Exception:
                    continue

            if total_cataloged >= limit:
                break

        return total_cataloged

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Retorna resumo das estatísticas da biblioteca catalogada."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM video_references")
            total_videos = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM video_references WHERE usage_permission = 'authorized'")
            authorized_videos = cursor.fetchone()[0]

            cursor.execute("""
                SELECT c.name, COUNT(v.id) 
                FROM categories c 
                LEFT JOIN video_references v ON v.category_id = c.id 
                GROUP BY c.id
            """)
            category_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT AVG(engagement_rate) FROM video_references WHERE view_count > 0")
            avg_engagement = cursor.fetchone()[0] or 0.0

        return {
            "total_videos": total_videos,
            "target_initial": 3000,
            "progress_percent": round((total_videos / 3000) * 100, 1),
            "authorized_videos": authorized_videos,
            "category_distribution": category_counts,
            "average_engagement_rate": round(avg_engagement, 2)
        }
