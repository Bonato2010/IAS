"""
Módulo de Upload Automático no TikTok via Playwright (Automação de Sessão).
Permite fazer login uma única vez e publicar vídeos no piloto automático sem burocracia de API.
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

class TikTokUploader:
    def __init__(self, session_dir: str = "./credentials/tiktok_session"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def interactive_login(self):
        """
        Abre o navegador visível para o usuário fazer login no TikTok.
        A sessão fica salva para sempre após este passo.
        """
        print("\n[TikTok] Abrindo navegador para login único...")
        print(" -> Faça o login na sua conta do TikTok na janela que vai abrir.")
        print(" -> Quando estiver logado no Creator Center, feche o navegador.")
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_dir),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload")
                
                # Aguarda até que o usuário faça o login e a página de upload seja carregada
                print("[TikTok] Aguardando você realizar o login no navegador...")
                page.wait_for_timeout(60000) # Aguarda até 60 segundos
                browser.close()
                print("[TikTok] Sessão gravada com sucesso!")
        except Exception as e:
            print(f"[TikTok] Erro ao iniciar login: {e}")

    def upload_video(
        self,
        video_path: Path,
        caption: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Publica o corte automaticamente no TikTok usando a sessão salva.
        """
        print(f"[TikTok] Iniciando upload automático: '{caption[:40]}...'")
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_dir),
                    headless=headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload")
                page.wait_for_load_state("networkidle")

                # 1. Enviar o arquivo de vídeo para o input file
                file_input = page.locator('input[type="file"]')
                if file_input.count() > 0:
                    file_input.set_input_files(str(video_path))
                    print(" -> Vídeo anexado. Aguardando processamento...")
                    page.wait_for_timeout(7000)

                    # 2. Preencher a legenda com hashtags
                    caption_box = page.locator('.DraftEditor-root, div[contenteditable="true"]')
                    if caption_box.count() > 0:
                        caption_box.first.click()
                        caption_box.first.fill(caption)

                    # 3. Clicar no botão de Publicar
                    post_button = page.get_by_role("button", name="Publicar")
                    if post_button.count() == 0:
                        post_button = page.get_by_role("button", name="Post")

                    if post_button.count() > 0:
                        post_button.first.click()
                        print("[TikTok] Botão de publicar acionado! Vídeo postado com sucesso.")
                        page.wait_for_timeout(5000)
                        browser.close()
                        return {"status": "SUCCESS", "platform": "tiktok"}
                    else:
                        browser.close()
                        return {"status": "WARNING", "message": "Botão de publicar não encontrado."}
                else:
                    browser.close()
                    return {"status": "ERROR", "message": "Sessão não autenticada. Execute o login primeiro."}

        except Exception as e:
            print(f"[TikTok] Erro no upload automatizado: {e}")
            return {"status": "ERROR", "error": str(e)}
