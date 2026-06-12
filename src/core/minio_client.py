from minio import Minio
from src.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)

# ─── Client MinIO ──────────────────────────────────────
# Une seule instance partagée par toute l'application
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def file_exists(bucket: str, file: str) -> bool:
    """
    Vérifie qu'un fichier existe dans un bucket donné.
    Retourne True si le fichier existe, False sinon.
    """
    try:
        minio_client.stat_object(bucket, file)
        return True
    except Exception:
        return False


def download_to_file(bucket: str, file: str, destination: str) -> None:
    """
    Télécharge un fichier depuis MinIO vers un chemin local (ex: /tmp/).
    Utilise fget_object qui télécharge par morceaux (stream), sans tout
    charger en mémoire.
    """
    minio_client.fget_object(bucket, file, destination)


def upload_from_file(bucket: str, file: str, source: str) -> None:
    """
    Upload un fichier local (ex: /tmp/output.csv) vers MinIO.
    Utilise fput_object qui transfère par morceaux (stream upload).
    """
    minio_client.fput_object(bucket, file, source)