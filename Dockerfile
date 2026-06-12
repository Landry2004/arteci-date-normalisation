# ─── Étape 1 : Build (compilation des dépendances) ───
FROM python:3.11-alpine3.22 AS builder

WORKDIR /app

# Outils de compilation pour les dépendances Alpine (Polars inclus)
RUN apk add --no-cache gcc musl-dev libffi-dev g++

COPY requirements.txt .

# Installation des dépendances dans un dossier local (--user)
RUN pip install --no-cache-dir --user -r requirements.txt


# ─── Étape 2 : Image finale (légère et sécurisée) ───
FROM python:3.11-alpine3.22 AS runner

WORKDIR /app

# Création d'un utilisateur non-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copie des dépendances avec les bons droits pour appuser
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copie du code source avec les bons droits
COPY --chown=appuser:appgroup ./src ./src

# Variables d'environnement
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Bascule sur l'utilisateur non-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]