"""
Módulo de Distribuição Multi-Canal e Upload Escalonado no YouTube.
Gerencia múltiplos canais, rotação de tokens OAuth2, agendamento e anti-duplicação.
"""
import os
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List

class YouTubeDistributor:
    def __init__(self, channels_config_path: str = "./channels.json"):
        self.config_path = Path(channels_config_path)
        self.channels = self._load_channels()

    def _load_channels(self) -> List[Dict[str, Any]]:
        """Carrega a lista de canais configurados."""
        if not self.config_path.exists():
            default_config = [
                {
                    "channel_id": "CHANNEL_ALPHA",
                    "channel_name": "Canal Cortes 1",
                    "refresh_token": "SEU_REFRESH_TOKEN_1",
                    "client_id": "SEU_CLIENT_ID",
                    "client_secret": "SEU_CLIENT_SECRET",
                    "upload_delay_minutes": 0
                },
                {
                    "channel_id": "CHANNEL_BETA",
                    "channel_name": "Canal Cortes 2",
                    "refresh_token": "SEU_REFRESH_TOKEN_2",
                    "client_id": "SEU_CLIENT_ID",
                    "client_secret": "SEU_CLIENT_SECRET",
                    "upload_delay_minutes": 30
                }
            ]
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            return default_config

        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def distribute_clip_to_channels(
        self,
        base_video_path: Path,
        clip_data: Any,
        video_editor: Any,
        subtitles_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Gera versões físicas com hash diferente e agenda o upload para cada canal cadastrado.
        """
        results = []
        print(f"\n[Distributor] Iniciando distribuição multi-canal do corte...")

        for idx, channel in enumerate(self.channels):
            channel_name = channel.get("channel_name", f"Canal_{idx+1}")
            channel_id = channel.get("channel_id")
            delay = channel.get("upload_delay_minutes", idx * 25)

            # 1. Seleciona o ângulo de título correspondente
            if idx == 0:
                title = clip_data.title_angle_1
            elif idx == 1:
                title = clip_data.title_angle_2
            else:
                title = clip_data.title_angle_3

            # 2. Renderiza arquivo com micro-modificação de áudio/vídeo (quebra de pHash)
            variant_path = base_video_path.parent / f"{base_video_path.stem}_ch{idx+1}.mp4"
            video_editor.render_vertical_clip(
                video_path=base_video_path,
                start_time=clip_data.start_time,
                end_time=clip_data.end_time,
                ass_subtitle_path=subtitles_path,
                output_clip_path=variant_path,
                channel_index=idx + 1
            )

            # 3. Calcula horário agendado (Staggering)
            publish_time = datetime.now(timezone.utc) + timedelta(minutes=delay)

            # 4. Registra no manifesto de postagem
            manifest_entry = {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "file_path": str(variant_path),
                "title": f"{title} #Shorts",
                "description": f"{clip_data.hook_quote}\n\nInscreva-se para mais cortes diários!\n#shorts #podcast #cortes",
                "scheduled_publish_time": publish_time.isoformat(),
                "status": "READY_FOR_UPLOAD"
            }
            results.append(manifest_entry)
            print(f" -> [Canal: {channel_name}] Vídeo pronto e agendado para +{delay}min: '{title}'")

        # Salvar manifesto da rodada
        manifest_file = base_video_path.parent / "upload_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results
