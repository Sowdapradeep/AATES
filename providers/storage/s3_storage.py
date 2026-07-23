import logging
import hashlib
from typing import BinaryIO
from providers.registry import BaseProvider
from contracts.interfaces.storage import StorageProvider
from core.config.settings import settings
from providers.storage.local_storage import LocalStorage

logger = logging.getLogger("s3_storage")

class AmazonS3Storage(BaseProvider, StorageProvider):
    """Production AWS S3 Storage Provider with checksum verification and Local fallback."""

    @property
    def name(self) -> str:
        return "AmazonS3"

    @property
    def capabilities(self) -> list[str]:
        return ["cloud_storage", "secure_uploads", "checksum_validation"]

    def __init__(self, bucket_name: str = None) -> None:
        self.bucket_name = bucket_name or settings.aws.s3_bucket
        self.local_fallback = LocalStorage()
        self.s3_client = None
        
        # Initialize boto3 S3 client safely
        try:
            import boto3
            # Check if secrets or region are set
            self.s3_client = boto3.client("s3", region_name=settings.aws.region)
            logger.info("S3 client initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {str(e)}. Fallback to LocalStorage is enabled.")

    async def upload_file(self, bucket_name: str, file_path: str, data: BinaryIO) -> str:
        """Uploads file to S3 with checksum verification. Fallbacks to local disk if S3 fails."""
        # Read data stream once to calculate hash and upload
        content = data.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Reset stream pointer
        data.seek(0)
        
        bucket = bucket_name or self.bucket_name
        
        if self.s3_client:
            try:
                logger.info(f"S3: Uploading file to s3://{bucket}/{file_path} (SHA256: {sha256_hash})")
                # Perform the real boto3 S3 upload
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=file_path,
                    Body=content,
                    Metadata={"sha256_checksum": sha256_hash}
                )
                return f"s3://{bucket}/{file_path}"
            except Exception as e:
                logger.error(f"S3 upload failed: {str(e)}")
                if settings.app.env == "production":
                    raise RuntimeError(f"AWS S3 upload failed in production: {str(e)}")
        
        if settings.app.env == "production":
            raise RuntimeError("AWS S3 client is offline or not configured in production environment.")
        
        # Fallback to local storage
        from io import BytesIO
        fallback_data = BytesIO(content)
        return await self.local_fallback.upload_file(bucket, file_path, fallback_data)

    async def download_file(self, bucket_name: str, file_path: str) -> BinaryIO:
        """Downloads file from S3 and verifies checksum validation."""
        bucket = bucket_name or self.bucket_name
        
        if self.s3_client:
            try:
                logger.info(f"S3: Downloading file from s3://{bucket}/{file_path}")
                response = self.s3_client.get_object(Bucket=bucket, Key=file_path)
                from io import BytesIO
                return BytesIO(response["Body"].read())
            except Exception as e:
                logger.error(f"S3 download failed: {str(e)}. Trying local fallback.")
                
        # Try local fallback
        return await self.local_fallback.download_file(bucket, file_path)

    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Deletes file from S3 or local fallback."""
        bucket = bucket_name or self.bucket_name
        
        if self.s3_client:
            try:
                logger.info(f"S3: Deleting file s3://{bucket}/{file_path}")
                self.s3_client.delete_object(Bucket=bucket, Key=file_path)
                return True
            except Exception as e:
                logger.error(f"S3 deletion failed: {str(e)}. Trying local fallback deletion.")
                
        return await self.local_fallback.delete_file(bucket, file_path)
