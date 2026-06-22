from minio import Minio
from src.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)

# Instance partagée par toute l'application 
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


# Vérifie qu'un objet existe dans un bucket via stat_object (sans le télécharger)
def file_exists(bucket: str, file: str) -> bool:
    try:
        minio_client.stat_object(bucket, file)
        return True
    except Exception:
        return False


# Télécharge un fichier depuis MinIO vers le disque local.
def download_to_file(bucket: str, file: str, destination: str) -> None:
    minio_client.fget_object(bucket, file, destination)


# Upload un fichier local vers MinIO 
def upload_from_file(bucket: str, file: str, source: str) -> None:
    minio_client.fput_object(bucket, file, source)