import os
import uuid
import polars as pl
import tempfile

from src.core.minio_client import file_exists, download_to_file
from src.core.csv_utils import detecter_separateur


# Dossier temporaire du système (compatible Windows et Linux)
TMP_DIR = tempfile.gettempdir()


def get_columns(bucket: str, file: str) -> list[str]:
    """Retourne la liste des colonnes d'un fichier CSV stocké dans MinIO."""
    if not file_exists(bucket, file):
        raise FileNotFoundError(
            f"Fichier '{file}' introuvable dans le bucket '{bucket}'."
        )

    # Chemin temporaire unique (évite les conflits entre requêtes)
    chemin_tmp = os.path.join(TMP_DIR, f"{uuid.uuid4()}_{os.path.basename(file)}")

    try:
        download_to_file(bucket, file, chemin_tmp)
        separateur = detecter_separateur(chemin_tmp)
        # n_rows=0 : lit seulement l'en-tête, sans charger les données
        df = pl.read_csv(chemin_tmp, separator=separateur, n_rows=0)

        return df.columns

    finally:
        if os.path.exists(chemin_tmp):
            os.remove(chemin_tmp)