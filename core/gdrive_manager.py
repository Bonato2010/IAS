"""
Módulo de Integração Oficial com Google Drive API v3 (Armazenamento Central de 5 TB).
Gerencia OAuth 2.0, controle de cotas, estrutura de pastas e transferências seguras.
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

class GDriveManager:
    TOTAL_CONTRACTED_BYTES = 5 * 1024 * 1024 * 1024 * 1024  # 5 TB

    REQUIRED_FOLDERS = [
        "00 - Banco de referências",
        "01 - Vídeos catalogados",
        "02 - Vídeos autorizados",
        "03 - Vídeos em análise",
        "04 - Inteligência e padrões",
        "05 - Roteiros e ideias",
        "06 - Produção",
        "07 - Vídeos finalizados",
        "08 - Thumbnails e materiais",
        "09 - Relatórios e métricas",
        "10 - Canais",
        "11 - Arquivos temporários",
        "12 - Backups e documentação"
    ]

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        config_file: Optional[str] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.creds_file = Path(credentials_file) if credentials_file else (base_dir / "credentials/gdrive_credentials.json")
        self.token_file = Path(token_file) if token_file else (base_dir / "credentials/gdrive_token.json")
        self.config_file = Path(config_file) if config_file else (base_dir / "config/gdrive_folders.json")
        self.creds_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.service = None
        self.folder_ids = self._load_folder_map()

    def _load_folder_map(self) -> Dict[str, str]:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_folder_map(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.folder_ids, f, indent=2, ensure_ascii=False)

    def is_authenticated(self) -> bool:
        """Verifica se existem credenciais e tokens salvos."""
        return self.token_file.exists() or bool(os.getenv("GDRIVE_REFRESH_TOKEN"))

    def get_service(self):
        """Inicializa e retorna o serviço oficial do Google Drive v3 com OAuth 2.0."""
        if self.service:
            return self.service

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = None
        SCOPES = ["https://www.googleapis.com/auth/drive"]

        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

        # Se expirado ou necessitando refresh
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        if not creds:
            raise PermissionError(
                "Google Drive não autenticado. Configure 'credentials/gdrive_credentials.json' "
                "e execute o login OAuth2 via interface ou CLI."
            )

        self.service = build("drive", "v3", credentials=creds)
        return self.service

    def get_storage_quota(self) -> Dict[str, Any]:
        """
        Consulta o armazenamento utilizado no Google Drive e calcula a capacidade restante dos 5 TB.
        """
        if not self.is_authenticated():
            return {
                "authenticated": False,
                "contracted_bytes": self.TOTAL_CONTRACTED_BYTES,
                "contracted_display": "5.0 TB",
                "used_bytes": 0,
                "used_display": "0.0 GB",
                "free_bytes": self.TOTAL_CONTRACTED_BYTES,
                "free_display": "5.0 TB",
                "used_percent": 0.0,
                "status": "Aguardando conexão OAuth2"
            }

        try:
            drive = self.get_service()
            about = drive.about().get(fields="storageQuota, user").execute()
            quota = about.get("storageQuota", {})

            # Drive Business ou Google One de 5TB retorna 'limit' e 'usage'
            used_bytes = int(quota.get("usage", 0))
            limit_bytes = int(quota.get("limit", self.TOTAL_CONTRACTED_BYTES))

            free_bytes = max(0, limit_bytes - used_bytes)
            used_percent = round((used_bytes / limit_bytes) * 100, 2) if limit_bytes > 0 else 0.0

            return {
                "authenticated": True,
                "user_name": about.get("user", {}).get("displayName", "Usuário"),
                "user_email": about.get("user", {}).get("emailAddress", ""),
                "contracted_bytes": limit_bytes,
                "contracted_display": f"{limit_bytes / (1024**4):.1f} TB",
                "used_bytes": used_bytes,
                "used_display": f"{used_bytes / (1024**3):.2f} GB",
                "free_bytes": free_bytes,
                "free_display": f"{free_bytes / (1024**4):.2f} TB",
                "used_percent": used_percent,
                "status": "Conectado e Sincronizado"
            }
        except Exception as e:
            return {
                "authenticated": False,
                "error": str(e),
                "status": f"Erro de conexão: {str(e)}"
            }

    def setup_drive_structure(self) -> Dict[str, str]:
        """
        Cria automaticamente a árvore completa de 13 pastas obrigatórias e as 20 subpastas de canais no Drive.
        """
        drive = self.get_service()
        print("[GDrive] Verificando e criando estrutura 'CENTRAL SHORTS' no Google Drive...")

        # 1. Pasta Raiz 'CENTRAL SHORTS'
        root_id = self.folder_ids.get("root")
        if not root_id:
            root_id = self._create_or_get_folder(drive, "CENTRAL SHORTS", parent_id=None)
            self.folder_ids["root"] = root_id

        # 2. As 13 Pastas Principais
        for folder_name in self.REQUIRED_FOLDERS:
            if folder_name not in self.folder_ids:
                f_id = self._create_or_get_folder(drive, folder_name, parent_id=root_id)
                self.folder_ids[folder_name] = f_id

        # 3. As 20 Subpastas dentro de '10 - Canais'
        channels_parent_id = self.folder_ids.get("10 - Canais")
        for i in range(1, 21):
            channel_folder_name = f"Canal {i:02d}"
            key_name = f"canal_{i:02d}"
            if key_name not in self.folder_ids:
                c_id = self._create_or_get_folder(drive, channel_folder_name, parent_id=channels_parent_id)
                self.folder_ids[key_name] = c_id

        self._save_folder_map()
        print(f"[GDrive] Estrutura completa de {len(self.folder_ids)} pastas configurada no Drive!")
        return self.folder_ids

    def _create_or_get_folder(self, drive, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Busca se a pasta já existe; se não, cria."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        res = drive.files().list(q=query, fields="files(id, name)").execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]

        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = drive.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")

    def upload_file(
        self,
        local_path: Path,
        folder_category: str = "07 - Vídeos finalizados",
        delete_local_after: bool = True
    ) -> Dict[str, Any]:
        """
        Envia um vídeo ou asset para o Google Drive com chunking e remove o arquivo local se solicitado.
        Garante que o computador local NUNCA vire depósito de vídeos.
        """
        drive = self.get_service()
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Arquivo local não encontrado: {local_path}")

        # Obtém ID da pasta destino
        parent_folder_id = self.folder_ids.get(folder_category, self.folder_ids.get("root"))

        from googleapiclient.http import MediaFileUpload

        file_metadata = {
            "name": local_path.name,
            "parents": [parent_folder_id] if parent_folder_id else []
        }

        media = MediaFileUpload(
            str(local_path),
            resumable=True,
            chunksize=10 * 1024 * 1024  # 10 MB chunks para alta eficiência
        )

        print(f"[GDrive] Enviando '{local_path.name}' para a pasta '{folder_category}' no Drive...")
        request = drive.files().create(body=file_metadata, media_body=media, fields="id, name, webViewLink, size")

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f" -> Progresso upload Drive: {int(status.progress() * 100)}%")

        file_id = response.get("id")
        web_link = response.get("webViewLink")
        print(f"[GDrive] Upload concluído com sucesso! File ID: {file_id}")

        # REGRA MANDATÓRIA: Limpar o arquivo local após o upload confirmado no Drive
        if delete_local_after:
            try:
                local_path.unlink()
                print(f"[GDrive] Arquivo local temporário removido com sucesso: {local_path.name}")
            except Exception as e:
                print(f"[GDrive] Aviso: Falha ao deletar arquivo local ({e})")

        return {
            "file_id": file_id,
            "web_link": web_link,
            "file_name": local_path.name,
            "folder": folder_category,
            "status": "UPLOADED"
        }
