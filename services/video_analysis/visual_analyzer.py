"""
IAS Video Analysis - Visual Analyzer (OpenCV)
Análise visual de movimento, composição e cálculo de Smart Crop 9:16 para centralização de personagens.
"""
import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

class OpenCVVisualAnalyzer:
    """Análise visual assistida por OpenCV para composição vertical de Shorts."""

    def __init__(self):
        self.available = hasattr(cv2, "__version__")

    def analyze_framing_and_motion(self, video_path: str, max_frames: int = 60) -> Dict[str, Any]:
        """
        Analisa intensidade de movimento e calcula a melhor posição de corte horizontal (Smart Crop).
        """
        if not os.path.exists(video_path):
            return {"error": f"Arquivo não encontrado: {video_path}"}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Não foi possível abrir o arquivo de vídeo via OpenCV"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        step = max(1, total_frames // max_frames)
        prev_gray = None
        motion_scores = []
        x_centers = []

        frame_idx = 0
        while cap.isOpened() and len(motion_scores) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Reduz para velocidade
                small = cv2.resize(gray, (320, 180))

                # 1. Detecção de Movimento
                if prev_gray is not None:
                    diff = cv2.absdiff(small, prev_gray)
                    motion_val = float(np.mean(diff))
                    motion_scores.append(motion_val)

                    # 2. Localização do Centro de Atenção (Centro de Massa do movimento/saliência)
                    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                    moments = cv2.moments(thresh)
                    if moments["m00"] > 0:
                        cx = (moments["m10"] / moments["m00"]) / 320.0 # 0.0 a 1.0 relativo
                        x_centers.append(cx)
                    else:
                        x_centers.append(0.5)
                else:
                    motion_scores.append(0.0)
                    x_centers.append(0.5)

                prev_gray = small

            frame_idx += 1

        cap.release()

        avg_motion = float(np.mean(motion_scores)) if motion_scores else 0.0
        # Média ponderada do centro horizontal do sujeito (0.5 = centro exato)
        median_x = float(np.median(x_centers)) if x_centers else 0.5
        # Mantém entre 0.2 e 0.8 para evitar cortar bordas pretas
        clamped_x = max(0.25, min(0.75, median_x))

        # Enquadramento estimado
        shot_type = "Medium Shot"
        if avg_motion > 15.0:
            shot_type = "High-Energy Action / Dynamic"
        elif avg_motion < 3.0:
            shot_type = "Static Talk / Close-Up"

        # Constrói expressão de crop para FFmpeg:
        # Se clamped_x = 0.5 -> '(iw-ow)/2'
        # Se clamped_x > 0.5 (sujeito à direita) -> desloca offset x para direita
        crop_expr = f"(iw-ow)*{clamped_x:.3f}"

        return {
            "engine": f"OpenCV {cv2.__version__}",
            "original_resolution": f"{orig_width}x{orig_height}",
            "aspect_ratio": round(orig_width / max(1, orig_height), 2),
            "average_motion_score": round(avg_motion, 2),
            "estimated_shot_type": shot_type,
            "recommended_crop_center_x": round(clamped_x, 3),
            "ffmpeg_crop_offset_x": crop_expr,
            "smart_crop_applied": abs(clamped_x - 0.5) > 0.05
        }
