import os
import uuid
import tempfile
import logging
import polars as pl
from opentelemetry import trace

from src.core.minio_client import file_exists, download_to_file, upload_from_file
from src.core.csv_utils import detecter_separateur
from src.core.date_processor import normalize_column
from src.config import BUCKET_PROCESSED

TMP_DIR = tempfile.gettempdir()

tracer = trace.get_tracer("arteci-api")
logger = logging.getLogger("arteci-api")


def process_date(
    bucket: str,
    file: str,
    date_columns: list[str],
    date_formats: list[str],
) -> list[dict]:
    logger.info(
        f"POST /processDate | bucket={bucket} | file={file} | "
        f"colonnes={date_columns} | formats={date_formats}"
    )

    # Validation : fichier présent
    if not file_exists(bucket, file):
        logger.error(f"Fichier introuvable | bucket={bucket} | file={file}")
        raise FileNotFoundError(
            f"Fichier '{file}' introuvable dans le bucket '{bucket}'."
        )

    # Validation : colonnes = formats
    if len(date_columns) != len(date_formats):
        logger.error("Nombre de colonnes et de formats différent")
        raise ValueError(
            "Le nombre de colonnes et de formats doit être identique."
        )

    nom_base = os.path.basename(file)
    chemin_input = os.path.join(TMP_DIR, f"{uuid.uuid4()}_in_{nom_base}")
    chemin_output = os.path.join(TMP_DIR, f"{uuid.uuid4()}_out_{nom_base}")

    try:
        # SPAN 1 : Lecture depuis MinIO
        with tracer.start_as_current_span("lecture_minio") as span:
            download_to_file(bucket, file, chemin_input)
            separateur = detecter_separateur(chemin_input)
            df = pl.read_csv(chemin_input, separator=separateur)
            span.set_attribute("fichier.lignes", len(df))
            span.set_attribute("fichier.separateur", separateur)
            logger.info(f"Fichier lu | lignes={len(df)} | separateur={separateur}")

        # Validation : colonnes existent
        for col in date_columns:
            if col not in df.columns:
                logger.error(f"Colonne inexistante | colonne={col}")
                raise ValueError(
                    f"La colonne '{col}' n'existe pas dans le fichier."
                )

        # SPAN 2 : Traitement (normalisation)
        with tracer.start_as_current_span("traitement_normalisation") as span:
            for col, fmt in zip(date_columns, date_formats):
                df = normalize_column(df, col, fmt)
            span.set_attribute("colonnes.traitees", len(date_columns))
            logger.info(f"Normalisation terminée | colonnes={len(date_columns)}")

        # SPAN 3 : Écriture dans MinIO
        with tracer.start_as_current_span("ecriture_minio") as span:
            df.write_csv(chemin_output, separator=separateur)
            upload_from_file(BUCKET_PROCESSED, file, chemin_output)
            span.set_attribute("fichier.destination", BUCKET_PROCESSED)
            logger.info(f"Fichier écrit | bucket={BUCKET_PROCESSED} | file={file}")

        # Aperçu des 100 premières lignes
        preview = df.head(100).to_dicts()
        logger.info(f"Traitement réussi | total_lignes={len(df)}")

        return preview

    finally:
        for chemin in (chemin_input, chemin_output):
            if os.path.exists(chemin):
                os.remove(chemin)