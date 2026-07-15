import abc
from typing import BinaryIO

class StorageProvider(abc.ABC):
    """Abstract interface defining required storage provider capabilities."""
    
    @abc.abstractmethod
    async def upload_file(self, bucket_name: str, file_path: str, data: BinaryIO) -> str:
        """Uploads a binary data stream and returns the absolute remote storage URI."""
        pass

    @abc.abstractmethod
    async def download_file(self, bucket_name: str, file_path: str) -> BinaryIO:
        """Downloads a binary file and returns a binary reader object."""
        pass

    @abc.abstractmethod
    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Deletes a file from the repository, returning True if successful."""
        pass
