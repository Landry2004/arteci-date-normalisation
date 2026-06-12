import os
import uuid
import polars as pl
import tempfile

from src.core.minio_client import file_exists, download_to_file
from src.core.csv_utils import detecter_separateur


# Dossier temporaire du système (compatible Windows et Linux)
TMP_DIR = tempfile.gettempdir()


def get_columns(bucket: str, file: str) -> list[str]:
    """
    Récupère la liste des colonnes d'un fichier stocké dans MinIO.

    Étapes :
    1. Vérifier que le fichier existe
    2. Télécharger le fichier dans /tmp/
    3. Détecter le séparateur
    4. Lire uniquement l'en-tête (n_rows=0) pour avoir les colonnes
    5. Nettoyer /tmp/
    """
    # 1. Vérifier l'existence
    if not file_exists(bucket, file):
        raise FileNotFoundError(
            f"Fichier '{file}' introuvable dans le bucket '{bucket}'."
        )

    # Chemin temporaire unique (évite les conflits entre requêtes)
    chemin_tmp = os.path.join(TMP_DIR, f"{uuid.uuid4()}_{os.path.basename(file)}")

    try:
        # 2. Télécharger dans /tmp/
        download_to_file(bucket, file, chemin_tmp)

        # 3. Détecter le séparateur
        separateur = detecter_separateur(chemin_tmp)

        # 4. Lire uniquement l'en-tête (n_rows=0 = aucune ligne de données)
        df = pl.read_csv(chemin_tmp, separator=separateur, n_rows=0)

        return df.columns

    finally:
        # 5. Nettoyer le fichier temporaire
        if os.path.exists(chemin_tmp):
            os.remove(chemin_tmp)