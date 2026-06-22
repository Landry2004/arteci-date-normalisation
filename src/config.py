import os

# ─── Configuration MinIO ───────────────────────────────
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")

# Identifiants d'accès MinIO
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# Connexion sécurisée (HTTPS) ou non
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# ─── Buckets ───────────────────────────────────────────
# Bucket cible pour les fichiers traités (écriture en place)
BUCKET_PROCESSED = os.getenv("MINIO_PROCESSED_BUCKET", "processeddata")