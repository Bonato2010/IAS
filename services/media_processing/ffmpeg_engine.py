"""
IAS Media Processing Engine (FFmpeg)
Renderização audiovisual de alto desempenho para YouTube Shorts (9:16 vertical),
normalização de áudio (EBU R128) e perfis anti-duplicação.
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

class FFmpegEngine:
    """Motor de processamento audiovisual baseado em FFmpeg."""

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.binary_path = ffmpeg_bin or self._find_ffmpeg()
        self.available = bool(self.binary_path and os.path.exists(self.binary_path))

    def _find_ffmpeg(self) -> Optional[str]:
        # 1. Checa PATH do sistema
        in_path = shutil.which("ffmpeg")
        if in_path:
            return in_path

        # 2. Checa caminho conhecido do WinGet
        winget_path = Path(r"C:\Users\jcvse\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe")
        if winget_path.exists():
            return str(winget_path)

        # 3. Busca recursiva no AppData
        appdata_local = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\jcvse\AppData\Local"))
        matches = list(appdata_local.glob("**/ffmpeg.exe"))
        if matches:
            return str(matches[0])

        return None

    def get_status(self) -> Dict[str, Any]:
        if not self.available:
            return {"available": False, "version": None, "binary_path": None}
        try:
            res = subprocess.run([self.binary_path, "-version"], capture_output=True, text=True, timeout=5)
            version_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg detectado"
            return {
                "available": True,
                "version": version_line,
                "binary_path": self.binary_path
            }
        except Exception as e:
            return {"available": False, "version": None, "error": str(e), "binary_path": self.binary_path}

    def extract_audio(self, video_path: str, output_wav: str) -> bool:
        """Extrai áudio mono a 16kHz ideal para transcrição com Whisper."""
        if not self.available:
            raise RuntimeError("FFmpeg não está disponível no sistema.")
        
        cmd = [
            self.binary_path, "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def extract_frame(self, video_path: str, timestamp_sec: float, output_img: str) -> bool:
        """Extrai um frame estático no timestamp indicado para análise de cena ou thumbnail."""
        if not self.available:
            raise RuntimeError("FFmpeg não está disponível no sistema.")
        
        cmd = [
            self.binary_path, "-y",
            "-ss", str(timestamp_sec),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_img)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def render_vertical_short(
        self,
        input_video: str,
        output_path: str,
        start_sec: float,
        end_sec: float,
        ass_subtitles_path: Optional[str] = None,
        crop_offset_x: Optional[str] = None, # ex: '(iw-ow)/2' para centro
        channel_variant: int = 1,
        normalize_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Renderiza o corte em formato vertical (1080x1920, 9:16),
        queima legendas ASS estilizadas e aplica normalização EBU R128.
        """
        if not self.available:
            return {"success": False, "error": "FFmpeg não disponível"}

        duration = max(1.0, end_sec - start_sec)
        offset_x = crop_offset_x or "(iw-ow)/2"

        # Constrói o filter_complex
        filters = [
            f"[0:v]crop=ih*(9/16):ih:{offset_x}:0,scale=1080:1920"
        ]

        # Variante de canal (anti-duplicação se for canal secundário)
        if channel_variant > 1:
            # Leve ajuste de saturação, contraste e matiz
            filters.append("eq=contrast=1.03:saturation=1.04:brightness=0.01")

        # Queima de legenda ASS
        if ass_subtitles_path and os.path.exists(ass_subtitles_path):
            escaped_sub = str(ass_subtitles_path).replace("\\", "/").replace(":", "\\:")
            filters.append(f"subtitles='{escaped_sub}'")

        v_filter_chain = ",".join(filters) + "[v]"

        # Áudio: normalização de loudness broadcast (-14 LUFS para YouTube Shorts / Reels)
        a_filter = "loudnorm=I=-14:LRA=7:tp=-1.5"
        if channel_variant > 1:
            a_filter += ",atempo=1.008" # Pequena alteração de velocidade imperceptível

        cmd = [
            self.binary_path, "-y",
            "-ss", str(start_sec),
            "-to", str(end_sec),
            "-i", str(input_video),
            "-filter_complex", v_filter_chain,
            "-map", "[v]",
            "-map", "0:a",
            "-filter:a", a_filter,
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "duration_sec": duration,
                    "size_mb": round(size_mb, 2),
                    "resolution": "1080x1920 (9:16)",
                    "variant": channel_variant
                }
            else:
                return {
                    "success": False,
                    "error": res.stderr[-500:] if res.stderr else "Erro desconhecido na renderização"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
