import os
import uuid
import tempfile
import polars as pl

from src.core.minio_client import file_exists, download_to_file, upload_from_file
from src.core.csv_utils import detecter_separateur
from src.core.date_processor import normalize_column
from src.config import BUCKET_PROCESSED

TMP_DIR = tempfile.gettempdir()


def process_date(
    bucket: str,
    file: str,
    date_columns: list[str],
    date_formats: list[str],
) -> list[dict]:
    # Validation : fichier présent dans le bucket source
    if not file_exists(bucket, file):
        raise FileNotFoundError(
            f"Fichier '{file}' introuvable dans le bucket '{bucket}'."
        )

    # Validation : autant de colonnes que de formats
    if len(date_columns) != len(date_formats):
        raise ValueError(
            "Le nombre de colonnes et de formats doit être identique."
        )

    # Chemins temporaires uniques
    nom_base = os.path.basename(file)
    chemin_input = os.path.join(TMP_DIR, f"{uuid.uuid4()}_in_{nom_base}")
    chemin_output = os.path.join(TMP_DIR, f"{uuid.uuid4()}_out_{nom_base}")

    try:
        # 1. Télécharger depuis raw
        download_to_file(bucket, file, chemin_input)

        # 2. Détecter le séparateur
        separateur = detecter_separateur(chemin_input)

        # 3. Lire le fichier
        df = pl.read_csv(chemin_input, separator=separateur)

        # Validation : les colonnes existent
        for col in date_columns:
            if col not in df.columns:
                raise ValueError(
                    f"La colonne '{col}' n'existe pas dans le fichier."
                )

        # 4. Normaliser chaque colonne de date
        for col, fmt in zip(date_columns, date_formats):
            df = normalize_column(df, col, fmt)

        # 5. Écrire le résultat traité
        df.write_csv(chemin_output, separator=separateur)

        # 6. Upload vers processeddata (même nom de fichier)
        upload_from_file(BUCKET_PROCESSED, file, chemin_output)

        # 7. Aperçu des 100 premières lignes
        preview = df.head(100).to_dicts()

        return preview

    finally:
        # 8. Nettoyage des fichiers temporaires
        for chemin in (chemin_input, chemin_output):
            if os.path.exists(chemin):
                os.remove(chemin)