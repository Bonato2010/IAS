"""
Script de Autenticação Inicial OAuth 2.0 do Google Drive 5 TB com Logging Detalhado.
"""
import sys
import os
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Mirror path
PODCAST_CUTTER_DIR = Path(r"C:\Users\jcvse\podcast_cutter")

LOG_FILE = BASE_DIR / "auth_log.txt"

def log(msg):
    print(msg)
    sys.stdout.flush()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

# Limpa log anterior
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("Iniciando auth_drive...\n")

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from core.gdrive_manager import GDriveManager

    CREDS_FILE = BASE_DIR / "credentials/gdrive_credentials.json"
    TOKEN_FILE = BASE_DIR / "credentials/gdrive_token.json"
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    log(f"[1/4] Verificando credenciais: {CREDS_FILE}")
    if not CREDS_FILE.exists():
        log(f"ERRO: Arquivo não encontrado: {CREDS_FILE}")
        sys.exit(1)

    log("[2/4] Abrindo navegador para autorização OAuth 2.0...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    
    # Executa o servidor local de autenticação
    creds = flow.run_local_server(
        port=0,
        authorization_prompt_message="Abra o seguinte link no seu navegador caso não tenha aberto automaticamente:\n{url}\n",
        success_message="Autenticação com o Google Drive concluída com sucesso! Pode fechar esta aba e retornar ao terminal."
    )

    log(f"[3/4] Salvando token em: {TOKEN_FILE}")
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as token:
        token.write(creds.to_json())
        
    # Copia para o espelho podcast_cutter também
    try:
        mirror_token = PODCAST_CUTTER_DIR / "credentials/gdrive_token.json"
        mirror_token.parent.mkdir(parents=True, exist_ok=True)
        with open(mirror_token, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    except Exception as me:
        log(f"Aviso ao espelhar token: {me}")
        
    log("[OK] Token gravado com sucesso!")

    log("[4/4] Criando as 13 pastas da CENTRAL SHORTS no seu Google Drive 5 TB...")
    mgr = GDriveManager()
    folders = mgr.setup_drive_structure()
    quota = mgr.get_storage_quota()

    log("=" * 65)
    log("   CONEXÃO CONCLUÍDA COM SUCESSO!")
    log(f"   Usuário: {quota.get('user_name')} ({quota.get('user_email')})")
    log(f"   Capacidade Total: {quota.get('contracted_display')}")
    log(f"   Espaço Livre: {quota.get('free_display')}")
    log(f"   Pastas Criadas no Drive: {len(folders)}")
    log("=" * 65)
    print("\nPressione ENTER para finalizar...")
    input()

except Exception as e:
    err_msg = f"\n[ERRO NA AUTENTICAÇÃO]:\n{traceback.format_exc()}"
    log(err_msg)
    print("\nPressione ENTER para fechar...")
    input()
