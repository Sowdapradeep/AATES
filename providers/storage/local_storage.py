import os
import shutil
from typing import BinaryIO
from providers.registry import BaseProvider
from contracts.interfaces.storage import StorageProvider

class LocalStorage(BaseProvider, StorageProvider):
    """Local disk-backed file storage implementation."""
    
    @property
    def name(self) -> str:
        return "LocalStorage"

    @property
    def capabilities(self) -> list[str]:
        return ["local_read", "local_write"]
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def upload_file(self, bucket_name: str, file_path: str, data: BinaryIO) -> str:
        """Saves a binary file to the local directory."""
        target_dir = os.path.join(self.base_path, bucket_name)
        os.makedirs(target_dir, exist_ok=True)
        dest_path = os.path.join(target_dir, file_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(data, f)
        return f"file:///{os.path.abspath(dest_path)}"

    async def download_file(self, bucket_name: str, file_path: str) -> BinaryIO:
        """Opens a binary reader for a local file."""
        source_path = os.path.join(self.base_path, bucket_name, file_path)
        return open(source_path, "rb")

    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Deletes a local file if it exists."""
        source_path = os.path.join(self.base_path, bucket_name, file_path)
        if os.path.exists(source_path):
            os.remove(source_path)
            return True
        return False
