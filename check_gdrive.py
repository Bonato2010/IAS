import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from core.gdrive_manager import GDriveManager

mgr = GDriveManager()
quota = mgr.get_storage_quota()
print("STORAGE_QUOTA:", json.dumps(quota, ensure_ascii=False))

if quota.get("authenticated"):
    folders = mgr.setup_drive_structure()
    print("TOTAL_FOLDERS_CONFIGURED:", len(folders))
    print("ROOT_FOLDER_ID:", folders.get("root"))
else:
    print("STATUS: NOT_AUTHENTICATED_YET")
