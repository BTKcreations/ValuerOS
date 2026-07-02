"""
ValuerOS — MinIO client wrapper for S3-compatible object storage.
"""
from __future__ import annotations

from minio import Minio

from app.core.config import get_settings

settings = get_settings()

_minio_client: Minio | None = None


def get_minio_client() -> Minio:
    """Returns a singleton MinIO client instance."""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        # Ensure bucket exists (with a graceful fallback if MinIO is not running)
        try:
            if not _minio_client.bucket_exists(settings.minio_bucket):
                _minio_client.make_bucket(settings.minio_bucket)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to connect to MinIO bucket '{settings.minio_bucket}': {str(e)}. "
                "Continuing with local mock storage fallback."
            )
    return _minio_client