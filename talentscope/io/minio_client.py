# -*- coding: utf-8 -*-
import logging
from minio import Minio
from minio.error import S3Error
from talentscope.config import MinioConfig

logger = logging.getLogger("talentscope.minio")

class MinioHandler:
    def __init__(self):
        self.endpoint = MinioConfig.ENDPOINT
        self.access_key = MinioConfig.ACCESS_KEY
        self.secret_key = MinioConfig.SECRET_KEY
        self.secure = MinioConfig.SECURE
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            logger.info("MinIO client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None

    def upload_file(self, bucket_name: str, file_path: str, object_name: str) -> bool:
        """
        Uploads a file to the specified bucket.
        Returns True if successful, False otherwise.
        """
        # Retry connection if not initialized
        if not self.client:
            self._connect()
            
        if not self.client:
            logger.warning("MinIO client is not initialized. Skipping upload.")
            return False

        try:
            # Check if bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created.")

            # Upload
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
            )
            logger.info(f"File '{object_name}' uploaded to bucket '{bucket_name}'.")
            return True
        except S3Error as e:
            logger.error(f"MinIO S3 Error during upload: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during MinIO upload: {e}")
            return False

# Global instance
minio_client = MinioHandler()
