# ARTECI — API de Normalisation de Dates

API de standardisation des formats de date, développée dans le cadre du Challenge DevOps / Data Platform d'Artefact CI.

Elle lit des fichiers CSV depuis MinIO, normalise les colonnes de dates vers un format unique (`JJ-MM-AAAA HH:mm:ss`), et réécrit le fichier traité dans un bucket dédié. Elle gère les formats hétérogènes (français, anglais, ISO) y compris mélangés au sein d'une même colonne.

---

## Sommaire

- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Performances](#performances)
- [Prérequis](#prérequis)
- [Démarrage rapide](#démarrage-rapide)
- [Utilisation de l'API](#utilisation-de-lapi)
- [Observabilité](#observabilité)
- [Tests](#tests)
- [CI/CD](#cicd)
- [Déploiement Kubernetes](#déploiement-kubernetes)
- [Limites connues](#limites-connues)

---

## Architecture

```
Frontend → Bucket "raw" (MinIO) → API → Bucket "processeddata" (MinIO) → Aperçu (100 lignes)
```

Le flux est simple : un fichier brut est déposé dans `raw`, l'API le télécharge, normalise les colonnes de dates demandées, puis réécrit le résultat dans `processeddata` avec le même nom. En réponse, elle retourne les 100 premières lignes traitées pour validation rapide.

**Règles métier couvertes :**

- Formats DMY (français), MDY (anglais) et ISO, reconnus automatiquement
- Formats mixtes par ligne : si une date est incohérente avec le format déclaré (ex. mois > 12 en DMY), bascule automatique vers MDY
- Cellules invalides ou vides : conservées telles quelles, sans plantagge
- Erreurs explicites : 404 (fichier absent), 400 (colonne inexistante ou incohérence colonnes/formats), 500 (erreur serveur)

---

## Stack technique

Le projet repose sur **Python 3.11**, choisi pour la maturité de son écosystème et la rapidité de développement qu'il permet, un atout décisif dans le cadre d'un sprint de deux semaines.

L'API est construite avec **FastAPI**, un framework moderne offrant de bonnes performances asynchrones et une documentation interactive générée automatiquement, accessible via l'endpoint `/docs`.

Le cœur du traitement de données utilise **Polars**, une bibliothèque écrite en Rust, nativement multi-threadée et reposant sur le format mémoire Apache Arrow. C'est ce composant qui assure les performances élevées du projet.

Le stockage des fichiers est assuré par **MinIO**, une solution de stockage objet compatible avec l'API S3 d'Amazon, qui présente l'avantage de pouvoir être déployée localement très simplement.

L'application est empaquetée avec **Docker**, sur une base Alpine afin d'obtenir une image finale légère et sécurisée. L'**observabilité** est assurée par OpenTelemetry pour l'instrumentation et Signoz pour la visualisation des traces et des logs structurés. Le déploiement en production s'appuie sur **Kubernetes**, et l'intégration ainsi que la livraison continues sont automatisées via **GitHub Actions**.

### Pourquoi Polars et pas Pandas

Ce n'est pas une préférence — c'est une mesure. Benchmark sur le fichier "lst_of_users_anon_2.csv", même machine, même données :

| Outil  | Temps     |
|--------|-----------|
| Pandas | 51.45s    |
| Polars | **0.63s** |

Polars est 81x plus rapide ici parce qu'il parallélise nativement sur les cœurs disponibles et utilise Apache Arrow en mémoire. Pandas est mono-threadé. Sur le fichier de 931 Mo, Pandas aurait probablement crashé en OOM avant de finir.

Le traitement utilise `read_csv` / `write_csv` en mémoire (pas de streaming). Ce choix est appuyé par la mesure : sur 931 Mo, le pic mémoire observé est 1.7 Go sur 8 Go disponibles — la marge est suffisante.

---

## Performances

Benchmarks réalisés dans les conditions de l'évaluation (conteneur Docker, 4 CPU / 8 Go, Alpine 3.22) :

| Fichier   | Taille  | Lignes      | Temps cible | Temps mesuré  |
|-----------|---------|-------------|-------------|---------------|
| Fichier 1 | 28 Mo   | 320 399     | ~20s        | **1.72s**     |
| Fichier 2 | 182 Mo  | 2 119 517   | ~50s        | **8.88s**     |
| Fichier 3 | 931 Mo  | 10 799 773  | ~2min       | **37.6s**     |

RAM max observée : 1.7 Go / 8 Go. CPU : 401 % (les 4 cœurs actifs).

---

## Prérequis

Pour lancer l'application il faut : **Docker** et **Docker Compose** v2.0+.

Pour retrouver les performances annoncées, il faut 4 cœurs et 8 Go de RAM — c'est ce qui est alloué dans `docker-compose.yml` et les manifests Kubernetes. Sur une machine moins dotée, ça fonctionne, mais plus lentement.

---

## Démarrage rapide

```bash
# 1. Cloner
git clone https://github.com/Landry2004/arteci-date-normalisation.git
cd arteci-date-normalisation

# 2. Lancer
docker-compose up -d
```

Ça lance MinIO, crée les buckets `raw` et `processeddata`, et démarre l'API depuis l'image Docker Hub (`landry225/arteci-api`).

> Pour reconstruire depuis le source : commenter la ligne `image:` et décommenter `build: .` dans le service `api` du `docker-compose.yml`.

```bash
# 3. Vérifier
curl http://localhost:8001/health
# → {"status":"healthy"}
```

**Interfaces disponibles :**
 
| Interface         | URL                         | Identifiants            |
|-------------------|-----------------------------|-------------------------|
| Documentation API | http://localhost:8001/docs  | —                       |
| Console MinIO     | http://localhost:9001       | minioadmin / minioadmin |

---

## Utilisation de l'API

Avant tout traitement, déposer le fichier CSV dans le bucket `raw` via la console MinIO.

### `GET /columns`

Retourne la liste des colonnes d'un fichier.

```
GET /columns?bucket=raw&file=mon_fichier.csv
```

```json
{
  "columns": ["CODE_LOGIN", "LOGIN", "DATE_CREATION", "DATE_DESACTIVATION"]
}
```

### `POST /processDate`

Normalise les colonnes de dates et réécrit le fichier dans `processeddata`.

**Requête :**

```json
{
  "bucket": "raw",
  "file": "mon_fichier.csv",
  "date_columns": ["DATE_CREATION", "DATE_DESACTIVATION"],
  "date_formats": ["MDY", "MDY"]
}
```

**Réponse :**

```json
{
  "status": "success",
  "preview": [
    {"CODE_LOGIN": "10000", "DATE_CREATION": "17-07-2019 00:00:00", "...": "..."}
  ]
}
```

Le fichier complet est dans `processeddata` ; l'aperçu (100 lignes) est là pour vérifier rapidement que la normalisation s'est bien passée.

---

## Observabilité

Chaque requête `POST /processDate` génère une trace OpenTelemetry couvrant le cycle complet :

```
POST /processDate          ← la requête complète (du début à la fin)
├── lecture_minio          ← télécharge le fichier depuis MinIO
├── traitement_normalisation  ← normalise les dates
├── ecriture_minio         ← écrit le fichier dans processeddata
└── réponse                ← renvoie le résultat (status + 100 lignes) au client
```

Des logs structurés (timestamp, niveau, contexte) accompagnent chaque étape.

### Visualisation avec Signoz (optionnel)

L'API tourne avec ou sans Signoz. Pour activer la visualisation :

```bash
# Lancer Signoz (stack officielle séparée)
git clone -b main https://github.com/SigNoz/signoz.git
cd signoz/deploy/docker
docker compose up -d

# Connecter l'API
docker network connect signoz-net arteci-api
```

Interface : http://localhost:8080, section **Traces**.

Signoz n'est pas fusionné dans le `docker-compose` principal — ça évite d'embarquer une stack tierce complexe dans un projet qui n'en a pas besoin par défaut.

---

## Tests

8 tests unitaires couvrant la logique de normalisation : DMY, MDY, bascule de format, formats mixtes, ISO, cellule invalide, cellule vide, cas complet.

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

---

## CI/CD

Pipeline GitHub Actions sur chaque push sur `main` :

1. Exécution des tests pytest
2. Si les tests passent : build de l'image Docker et push sur Docker Hub

Image publiée : [`landry225/arteci-api`](https://hub.docker.com/r/landry225/arteci-api)

---

## Déploiement Kubernetes

Le dossier `k8s/` contient trois manifests : `configmap.yaml` (la configuration), `deployment.yaml` (le déploiement de l'API avec ses ressources) et `service.yaml` (l'exposition réseau).

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

kubectl get pods
kubectl get service
```

Les ressources allouées dans `deployment.yaml` sont 4 CPU / 8 Gi. Les manifests fonctionnent à l'identique sur un cluster local (Docker Desktop, kind) ou cloud (EKS, GKE, AKS) — sur cloud, le `type: LoadBalancer` génère une adresse publique automatiquement.

## Limites connues

**Traitement in-memory** : validé sur le fichier de 931 Mo avec un pic à 1.7 Go. Pour des fichiers nettement plus volumineux, un traitement par chunks serait nécessaire — l'architecture le permettrait sans refonte majeure.

**Signoz séparé** : deux commandes supplémentaires pour l'activer, c'est documenté plus haut. Le choix est intentionnel.

**Dépôt initial dans `raw`** : manuel via la console MinIO (dans un vrai flux produit, ce serait géré côté frontend).

**Identifiants MinIO** : `minioadmin` par défaut, à changer en production.

---

Projet réalisé dans le cadre du Challenge Stagiaire DevOps — Artefact CI.  
Dépôt : https://github.com/Landry2004/arteci-date-normalisation
