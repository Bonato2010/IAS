"""
Módulo de Edição, Reenquadramento Vertical 9:16 e Geração de Legendas Dinâmicas.
"""
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class VideoEditor:
    def __init__(self, output_dir: str = "./workspace/clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_ass_subtitles(
        self,
        words: List[Dict[str, Any]],
        start_time: float,
        end_time: float,
        ass_path: Path
    ) -> Path:
        """
        Gera legendas dinâmicas no padrão ASS (Advanced SubStation Alpha)
        com estilo Hormozi / TikTok (palavras em destaque, borda espessa, fonte chamativa).
        """
        # Filtrar apenas as palavras que caem no intervalo do corte
        clip_words = [
            w for w in words
            if w["start"] >= (start_time - 0.2) and w["end"] <= (end_time + 0.2)
        ]

        # Cabeçalho do arquivo ASS
        ass_content = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            # Estilo: Amarelo (#00FFFF em BGR -> &H0000FFFF), Borda preta de 5px, Alinhamento centro-inferior
            "Style: Default,Arial Black,75,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,50,50,450,1",
            "Style: Highlight,Arial Black,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,0,0,1,7,4,2,50,50,450,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        # Criar frases curtas (3 a 5 palavras por tela) com destaque na palavra falada
        def format_time(t: float) -> str:
            rel_t = max(0.0, t - start_time)
            h = int(rel_t // 3600)
            m = int((rel_t % 3600) // 60)
            s = int(rel_t % 60)
            cs = int(round((rel_t - int(rel_t)) * 100))
            return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

        # Agrupar palavras em blocos visuais de 4
        chunk_size = 4
        for i in range(0, len(clip_words), chunk_size):
            chunk = clip_words[i:i + chunk_size]
            for curr_idx, active_word in enumerate(chunk):
                w_start = format_time(active_word["start"])
                w_end = format_time(active_word["end"])

                # Monta a frase com a palavra atual em destaque amarelo
                line_parts = []
                for idx, w in enumerate(chunk):
                    if idx == curr_idx:
                        line_parts.append(r"{\rHighlight}" + w["word"].upper() + r"{\rDefault}")
                    else:
                        line_parts.append(w["word"].upper())

                dialogue_text = " ".join(line_parts)
                ass_content.append(f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{dialogue_text}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_content))

        return ass_path

    def render_vertical_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        ass_subtitle_path: Path,
        output_clip_path: Path,
        channel_index: int = 1
    ) -> Path:
        """
        Corta o vídeo, reenquadra para 9:16 (1080x1920) centralizado e queima a legenda.
        Aplica também micro-alterações para quebrar o hash perceptual por canal.
        """
        print(f"[VideoEditor] Renderizando corte vertical 9:16: {output_clip_path.name}")
        duration = end_time - start_time

        # Escapando caminho do arquivo de legendas para o filtro do FFmpeg no Windows
        sub_filter_path = str(ass_subtitle_path).replace("\\", "/").replace(":", "\\:")

        # Filtro de micro-variação de áudio/vídeo por canal (Anti-Duplicate Detection)
        audio_tempo = 1.0 + (channel_index * 0.004) # Ex: 1.004, 1.008...
        contrast_boost = 1.0 + (channel_index * 0.01) # Ex: 1.01, 1.02...

        # Filtro de reenquadramento vertical 9:16:
        # Pega a altura original (ex: 1080), calcula largura vertical (1080 * 9/16 = 607.5)
        # e centraliza no meio do vídeo horizontal original.
        filter_complex = (
            f"[0:v]crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920,"
            f"eq=contrast={contrast_boost:.2f}:saturation=1.02,"
            f"subtitles='{sub_filter_path}'[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", str(video_path),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "0:a",
            "-filter:a", f"atempo={audio_tempo:.4f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_clip_path)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro no FFmpeg: {res.stderr}")

        print(f"[VideoEditor] Renderizado com sucesso: {output_clip_path}")
        return output_clip_path
