"""
Módulo de Upload Automático via YouTube Data API v3.
Gerencia OAuth2, quota e agendamento de Shorts.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class YouTubeUploader:
    def __init__(self, credentials_dir: str = "./credentials"):
        self.creds_dir = Path(credentials_dir)
        self.creds_dir.mkdir(parents=True, exist_ok=True)

    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list = None,
        publish_time_iso: Optional[str] = None,
        channel_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz o upload oficial do vídeo curto (Shorts) para o canal especificado.
        """
        print(f"[YouTubeUploader] Enviando '{title}' para o YouTube...")
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials

            tags = tags or ["shorts", "podcast", "cortes"]
            
            # Se existirem credenciais OAuth válidas configuradas
            if channel_config and "refresh_token" in channel_config:
                creds = Credentials(
                    token=None,
                    refresh_token=channel_config["refresh_token"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=channel_config.get("client_id"),
                    client_secret=channel_config.get("client_secret")
                )
                youtube = build("youtube", "v3", credentials=creds)

                body = {
                    "snippet": {
                        "title": title[:100],
                        "description": description,
                        "tags": tags,
                        "categoryId": "22"  # People & Blogs
                    },
                    "status": {
                        "privacyStatus": "private" if publish_time_iso else "public",
                        "selfDeclaredMadeForKids": False
                    }
                }
                if publish_time_iso:
                    body["status"]["publishAt"] = publish_time_iso

                media = MediaFileUpload(
                    str(video_path),
                    mimetype="video/mp4",
                    resumable=True,
                    chunksize=1024*1024*5
                )

                request = youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media
                )
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        print(f" -> Progresso upload YouTube: {int(status.progress() * 100)}%")

                video_id = response.get("id")
                print(f"[YouTubeUploader] Publicado com sucesso! https://youtube.com/shorts/{video_id}")
                return {"status": "SUCCESS", "video_id": video_id, "url": f"https://youtube.com/shorts/{video_id}"}

            else:
                print(f"[YouTubeUploader] Modo Simulação (Insira as credenciais no channels.json para envio real).")
                return {"status": "SIMULATED", "path": str(video_path), "title": title}

        except Exception as e:
            print(f"[YouTubeUploader] Erro no upload: {e}")
            return {"status": "ERROR", "error": str(e)}
