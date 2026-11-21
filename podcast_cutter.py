"""
Orquestrador Principal do Pipeline de Produção, Aprendizado e Postagem Automática.
"""
import argparse
import sys
from pathlib import Path

from core.downloader import MediaIngestor
from core.transcriber import AudioTranscriber
from core.hook_miner import HookMiner
from core.video_editor import VideoEditor
from core.youtube_distributor import YouTubeDistributor
from core.youtube_uploader import YouTubeUploader
from core.tiktok_uploader import TikTokUploader
from core.pattern_learner import PatternLearner

def run_pipeline(
    source_input: str,
    max_clips: int = 3,
    whisper_model: str = "base",
    auto_upload_youtube: bool = False,
    auto_upload_tiktok: bool = False
):
    print("=" * 65)
    print("      INICIANDO PIPELINE AUTOMATIZADO DE CORTES (YOUTUBE & TIKTOK)      ")
    print("=" * 65)

    ingestor = MediaIngestor()
    if source_input.startswith("http://") or source_input.startswith("https://"):
        video_path = ingestor.download_youtube(source_input)
    else:
        video_path = Path(source_input)
        if not video_path.exists():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")

    audio_path = ingestor.extract_audio(video_path)

    transcriber = AudioTranscriber(model_size=whisper_model)
    words_data = transcriber.transcribe_local_whisper(audio_path)
    full_transcript_text = transcriber.words_to_full_text(words_data)

    miner = HookMiner()
    selected_clips = miner.find_viral_moments(full_transcript_text, max_clips=max_clips)

    editor = VideoEditor()
    distributor = YouTubeDistributor()
    yt_uploader = YouTubeUploader() if auto_upload_youtube else None
    tk_uploader = TikTokUploader() if auto_upload_tiktok else None

    print(f"\n[Pipeline] Processando {len(selected_clips)} cortes selecionados...")
    for idx, clip in enumerate(selected_clips, 1):
        print(f"\n--- Processando Corte #{idx} [{clip.archetype.upper()}] (Score Viral: {clip.viral_score}/10) ---")
        print(f"Gancho: \"{clip.hook_quote}\"")
        print(f"Intervalo: {clip.start_time:.1f}s até {clip.end_time:.1f}s")

        ass_path = editor.output_dir / f"clip_{idx}_{int(clip.start_time)}.ass"
        editor.generate_ass_subtitles(
            words=words_data,
            start_time=clip.start_time,
            end_time=clip.end_time,
            ass_path=ass_path
        )

        manifest_entries = distributor.distribute_clip_to_channels(
            base_video_path=video_path,
            clip_data=clip,
            video_editor=editor,
            subtitles_path=ass_path
        )

        for entry in manifest_entries:
            clip_file = Path(entry["file_path"])
            title = entry["title"]
            desc = entry["description"]

            if auto_upload_youtube and yt_uploader:
                yt_uploader.upload_short(
                    video_path=clip_file,
                    title=title,
                    description=desc,
                    publish_time_iso=entry.get("scheduled_publish_time")
                )

            if auto_upload_tiktok and tk_uploader and "_ch1" in clip_file.name:
                tiktok_caption = f"{title} #shorts #podcast #cortes #viral"
                tk_uploader.upload_video(
                    video_path=clip_file,
                    caption=tiktok_caption
                )

    print("\n" + "=" * 65)
    print("  PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"  Vídeos prontos salvos em: {editor.output_dir}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automação End-to-End de Cortes com IA (YouTube & TikTok)")
    parser.add_argument("--source", "-s", help="URL do YouTube ou caminho do arquivo MP4 local")
    parser.add_argument("--clips", "-c", type=int, default=3, help="Quantidade de cortes a extrair")
    parser.add_argument("--whisper-model", "-w", default="base", help="Tamanho do modelo Whisper (tiny, base, small)")
    parser.add_argument("--upload-youtube", action="store_true", help="Faz upload automático dos cortes no YouTube")
    parser.add_argument("--upload-tiktok", action="store_true", help="Faz upload automático dos cortes no TikTok")
    parser.add_argument("--login-tiktok", action="store_true", help="Abre o navegador para conectar sua conta do TikTok")
    parser.add_argument("--learn", nargs="+", help="Treina a IA enviando uma ou mais URLs de Shorts de referência")

    args = parser.parse_args()

    # Modo de Aprendizado de Padrões Virais
    if args.learn:
        learner = PatternLearner()
        learner.learn_from_urls(args.learn)
        sys.exit(0)

    # Modo Login TikTok
    if args.login_tiktok:
        uploader = TikTokUploader()
        uploader.interactive_login()
        sys.exit(0)

    if not args.source:
        parser.print_help()
        sys.exit(1)

    run_pipeline(
        source_input=args.source,
        max_clips=args.clips,
        whisper_model=args.whisper_model,
        auto_upload_youtube=args.upload_youtube,
        auto_upload_tiktok=args.upload_tiktok
    )
