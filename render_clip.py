import json
import subprocess
from pathlib import Path

# Paths
base_dir = Path("C:/Users/jcvse/podcast_cutter")
subs_json = base_dir / "workspace/subs/8TpjD8D9tIo.pt.json3"
raw_video = base_dir / "workspace/downloads/corte_raw_1.mp4"
clips_dir = base_dir / "workspace/clips"
clips_dir.mkdir(parents=True, exist_ok=True)

ass_path = clips_dir / "corte_1.ass"
output_final_1 = clips_dir / "corte_1_final.mp4"
output_final_2 = clips_dir / "corte_1_canal2.mp4"

# 1. Carregar eventos de legenda do intervalo 184s a 228s
with open(subs_json, encoding="utf-8") as f:
    data = json.load(f)

start_offset = 184.0
clip_events = []

for ev in data.get("events", []):
    t_start = ev.get("tStartMs", 0) / 1000.0
    d_dur = ev.get("dDurationMs", 0) / 1000.0
    t_end = t_start + d_dur
    
    if t_start >= 184.0 and t_start <= 228.0:
        text = "".join(s.get("utf8", "") for s in ev.get("segs", [])).strip()
        text = text.replace(">>", "").strip()
        if text and text != "\n":
            rel_start = max(0.0, t_start - start_offset)
            rel_end = max(rel_start + 0.5, t_end - start_offset)
            clip_events.append((rel_start, rel_end, text))

def format_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

# 2. Gerar arquivo ASS com estilo viral TikTok / Hormozi
ass_lines = [
    "[Script Info]",
    "ScriptType: v4.00+",
    "PlayResX: 1080",
    "PlayResY: 1920",
    "ScaledBorderAndShadow: yes",
    "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Default,Arial,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,40,40,480,1",
    "Style: Highlight,Arial,72,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,0,0,1,7,3,2,40,40,480,1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
]

for start_t, end_t, text in clip_events:
    words = text.split()
    if not words:
        continue
    # Divide a frase e destaca
    formatted_start = format_ass_time(start_t)
    formatted_end = format_ass_time(end_t)
    
    # Destaca a primeira palavra chave em amarelo
    highlighted_text = r"{\c&H0000FFFF&}" + words[0].upper() + r"{\c&H00FFFFFF&} " + " ".join(words[1:]).upper()
    ass_lines.append(f"Dialogue: 0,{formatted_start},{formatted_end},Default,,0,0,0,,{highlighted_text}")

with open(ass_path, "w", encoding="utf-8") as f:
    f.write("\n".join(ass_lines))

print(f"[1/3] Legendas ASS geradas em: {ass_path}")

# 3. Renderizar com FFmpeg (Crop 9:16 + Escala 1080x1920 + Queima da Legenda)
ffmpeg_exe = r"C:\Users\jcvse\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe"
sub_filter_path = str(ass_path).replace("\\", "/").replace(":", "\\:")

filter_complex = f"[0:v]crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920,subtitles='{sub_filter_path}'[v]"

print("[2/3] Renderizando Vídeo 1 (YouTube Shorts / TikTok)...")
cmd_1 = [
    ffmpeg_exe, "-y",
    "-i", str(raw_video),
    "-filter_complex", filter_complex,
    "-map", "[v]",
    "-map", "0:a",
    "-c:v", "libx264",
    "-preset", "faster",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    str(output_final_1)
]
subprocess.run(cmd_1, check=True)
print(f" -> Concluído: {output_final_1}")

# 4. Renderizar Variante 2 (Anti-Duplicação para Canal 2)
print("[3/3] Renderizando Vídeo 2 (Variante para Canal Secundário)...")
filter_complex_2 = f"[0:v]crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920,eq=contrast=1.02:saturation=1.03,subtitles='{sub_filter_path}'[v]"
cmd_2 = [
    ffmpeg_exe, "-y",
    "-i", str(raw_video),
    "-filter_complex", filter_complex_2,
    "-map", "[v]",
    "-map", "0:a",
    "-filter:a", "atempo=1.008",
    "-c:v", "libx264",
    "-preset", "faster",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    str(output_final_2)
]
subprocess.run(cmd_2, check=True)
print(f" -> Concluído: {output_final_2}")
print("\nTODOS OS VÍDEOS FORAM RENDERIZADOS COM SUCESSO!")
