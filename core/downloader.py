"""
Módulo de Download e Ingestão de Mídia via yt-dlp ou arquivo local.
"""
import os
import subprocess
from pathlib import Path

class MediaIngestor:
    def __init__(self, output_dir: str = "./workspace/downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_youtube(self, url: str) -> Path:
        """
        Baixa o vídeo com a melhor qualidade de vídeo e áudio compatível.
        """
        print(f"[Ingestor] Baixando vídeo do YouTube: {url}")
        output_template = str(self.output_dir / "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro no download: {res.stderr}")

        # Identificar o arquivo baixado mais recente na pasta
        files = list(self.output_dir.glob("*.mp4"))
        if not files:
            raise FileNotFoundError("Nenhum arquivo MP4 encontrado após download.")
        latest_file = max(files, key=os.path.getctime)
        print(f"[Ingestor] Download concluído: {latest_file.name}")
        return latest_file

    def extract_audio(self, video_path: Path) -> Path:
        """
        Extrai o áudio em formato WAV mono 16kHz ideal para transcrição.
        """
        audio_path = video_path.with_suffix(".wav")
        print(f"[Ingestor] Extraindo áudio otimizado: {audio_path.name}")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(audio_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return audio_path
