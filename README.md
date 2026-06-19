# ARTECI — API de Normalisation de Dates

API de standardisation des formats de date, développée dans le cadre du Challenge DevOps / Data Platform d'Artefact CI.

Elle récupère un fichier CSV depuis MinIO, normalise les colonnes de dates vers un format unique (`JJ-MM-AAAA HH:mm:ss`), puis réécrit le fichier traité en place (écrasement). Elle gère les formats hétérogènes (français, anglais, ISO) y compris mélangés au sein d'une même colonne.
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

Cette API intervient à la **fin** d'une chaîne de validation. En amont, un fichier brut est déposé dans le bucket `raw`, puis une première étape de traitement le copie dans le bucket `processeddata`. Cette API récupère alors le fichier intermédiaire dans `processeddata`, normalise les colonnes de dates demandées, et **réécrit (écrase) le fichier en place** dans ce même bucket. En réponse, elle retourne les 100 premières lignes traitées pour validation rapide.

```
Bucket "raw" → [étapes amont] → Bucket "processeddata" → API (normalise + écrase en place) → Aperçu (100 lignes)

```
Le principe d'écriture est : **quel que soit le bucket reçu en paramètre, le fichier est écrasé dans ce même bucket** (écriture en place). En pratique, le bucket reçu est `processeddata`.


**Règles métier couvertes :**

- Formats DMY (français), MDY (anglais) et ISO, reconnus automatiquement
- Formats mixtes par ligne : si une date est incohérente avec le format déclaré (ex. mois > 12 en DMY), bascule automatique vers MDY
- Cellules invalides ou vides : conservées telles quelles, sans plantage
- Erreurs explicites : 404 (fichier absent), 400 (colonne inexistante ou incohérence colonnes/formats), 500 (erreur serveur)

---

## Stack technique

Le projet repose sur **Python 3.11**, choisi parce qu'il dispose de nombreuses bibliothèques prêtes à l'emploi et permet de développer rapidement, un atout décisif dans le cadre d'un sprint de deux semaines.

L'API est construite avec **FastAPI**, un framework moderne et rapide qui génère automatiquement une documentation interactive, accessible via l'endpoint `/docs`.

Le cœur du traitement de données utilise **Polars**, une bibliothèque écrite en Rust qui gagne en popularité grâce à sa rapidité et son efficacité mémoire. Elle utilise tous les cœurs du processeur en même temps et repose sur le format mémoire Apache Arrow, ce qui lui permet de surpasser Pandas dans la plupart des cas. C'est ce composant qui assure les performances élevées du projet.

Le stockage des fichiers est assuré par **MinIO**, une solution de stockage objet qui présente l'avantage de pouvoir être déployée localement très simplement (et compatible S3, le standard d'Amazon).

L'application est empaquetée avec **Docker**, sur une base Alpine afin d'obtenir une image finale légère et sécurisée. L'**observabilité** est assurée par OpenTelemetry pour l'instrumentation et Signoz pour la visualisation des traces et des logs structurés. Le déploiement en production s'appuie sur **Kubernetes**, et l'intégration ainsi que le déploiement continus sont automatisés via **GitHub Actions**.

### Pourquoi Polars et pas Pandas

Ce n'est pas une préférence, c'est une mesure. J'ai comparé les deux outils sur le même fichier (`lst_of_users_anon_2.csv`), même machine, mêmes données :

| Outil  | Temps     |
|--------|-----------|
| Pandas | 51.45s    |
| Polars | **0.63s** |

Polars est environ 80x plus rapide. La raison principale : Polars utilise **tous les cœurs du processeur en même temps**, alors que Pandas n'en utilise qu'un seul. Polars organise aussi les données en mémoire de façon plus efficace.

Sur le plus gros fichier (931 Mo), Pandas aurait probablement planté par manque de mémoire, là où Polars reste stable.

Le traitement charge le fichier entièrement en mémoire (lecture et écriture d'un coup, pas morceau par morceau). C'est un choix sûr : même sur 931 Mo, le maximum de mémoire utilisée est 1.7 Go sur 8 Go disponibles; il reste largement de la marge.


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

Avant tout traitement, le fichier CSV doit être présent dans le bucket `processeddata` (déposé par les étapes amont). Pour tester l'API de façon autonome, on peut y déposer manuellement un fichier via la console MinIO.

### `GET /columns`

Retourne la liste des colonnes d'un fichier.

```
GET /columns?bucket=processeddata&file=mon_fichier.csv
```

```json
{
  "columns": ["CODE_LOGIN", "LOGIN", "DATE_CREATION", "DATE_DESACTIVATION"]
}
```

### `POST /processDate`

Normalise les colonnes de dates et réécrit (écrase) le fichier en place dans le bucket reçu.

**Requête :**

```json
{
  "bucket": "processeddata",
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

La stack Signoz complète (collecteur OpenTelemetry, ClickHouse, interface) est **intégrée directement dans le `docker-compose.yml`** via le mécanisme `include`. Elle démarre donc automatiquement avec le reste du projet, sans installation séparée : la commande `docker-compose up -d` lance l'API, MinIO **et** Signoz ensemble.

### Visualiser les traces

L'interface Signoz est accessible sur `http://localhost:8080`.

Au tout premier lancement, Signoz demande de **créer un compte administrateur** (email, nom, mot de passe). Cette étape est nécessaire : elle initialise l'organisation interne de Signoz, sans laquelle le collecteur ne peut pas enregistrer les traces. Une fois le compte créé, lancez un traitement `POST /processDate`, puis ouvrez la section **Traces** : la trace `POST /processDate` y apparaît avec le détail de ses cinq étapes et leurs durées.



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

Le dossier `k8s/` contient quatre manifests :

- `minio.yaml` — déploiement et service de MinIO (le stockage)
- `configmap.yaml` — la configuration (variables d'environnement)
- `deployment.yaml` — le déploiement de l'API avec ses ressources (4 CPU / 8 Gi)
- `service.yaml` — l'exposition réseau de l'API

L'architecture déployée reproduit celle du `docker-compose` : MinIO et l'API tournent dans le cluster, l'API communiquant avec MinIO via le service interne `minio-service`.



### 1. Déployer MinIO puis l'API

L'ordre est important : MinIO doit être disponible avant l'API, car l'API se connecte à MinIO dès son démarrage pour lire et écrire les fichiers. Si MinIO n'est pas prêt, l'API ne peut pas fonctionner correctement.

```bash
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 2. Vérifier que les pods tournent

```bash
kubectl get pods
```

Les deux pods `arteci-api` et `minio` doivent être en statut `Running`.

### 3. Créer les buckets et déposer un fichier

MinIO démarre vide dans le cluster. Contrairement au `docker-compose` (où un service `minio-init` crée les buckets automatiquement), les manifests Kubernetes ne l'incluent pas — il faut donc créer les buckets manuellement. On ouvre un accès à sa console via un port-forward :

```bash
kubectl port-forward service/minio-service 9001:9001
```

Sur `http://localhost:9001` (identifiants `minioadmin` / `minioadmin`), créer les buckets `raw` et `processeddata`, puis déposer un fichier CSV dans `processeddata`.

### 4. Accéder à l'API

Dans un autre terminal, ouvrir un port-forward vers l'API :

```bash
kubectl port-forward service/arteci-api-service 8001:8000
```

L'API est alors accessible sur `http://localhost:8001`.

### 5. Vérifier le déploiement

```bash
# Santé de l'API
curl http://localhost:8001/health

# Lecture depuis MinIO
curl "http://localhost:8001/columns?bucket=processeddata&file=mon_fichier.csv"

# Traitement complet (lecture + normalisation + écrasement en place)
curl -X POST http://localhost:8001/processDate \
  -H "Content-Type: application/json" \
  -d '{"bucket":"processeddata","file":"mon_fichier.csv","date_columns":["DATE_CREATION"],"date_formats":["MDY"]}'
```

Si les trois répondent correctement, le déploiement est complet et fonctionnel.

### Portabilité

Ces manifests fonctionnent à l'identique sur un cluster local (Docker Desktop, kind) ou sur un cluster cloud (AWS EKS, Google GKE, Azure AKS). Sur un environnement cloud, le `type: LoadBalancer` du service de l'API génère automatiquement une adresse publique, ce qui dispense du port-forward.

> **Note** : dans le cluster, MinIO utilise un stockage éphémère (`emptyDir`) : les données sont perdues si le pod redémarre. C'est suffisant pour une démonstration, mais pour un usage en production il faudrait un volume persistant (PersistentVolumeClaim) afin de conserver les données entre redémarrages.


## Limites connues

**Traitement in-memory** : validé sur le fichier de 931 Mo avec un pic à 1.7 Go. Pour des fichiers nettement plus volumineux, il faudrait traiter le fichier par morceaux (au lieu de tout charger d'un coup) — l'architecture le permettrait sans refonte majeure.

**Création du compte Signoz** : au premier lancement, il faut créer un compte sur l'interface Signoz (`http://localhost:8080`) pour activer la collecte des traces. Cette étape est documentée dans la section Observabilité.

**Dépôt du fichier dans `processeddata`** : dans le flux réel, le fichier y est déposé par les étapes amont de la chaîne. Pour un test autonome, le dépôt se fait manuellement via la console MinIO.

**Identifiants MinIO** : `minioadmin` par défaut, à changer en production.

---

Projet réalisé dans le cadre du Challenge Stagiaire DevOps — Artefact CI.  
Dépôt : https://github.com/Landry2004/arteci-date-normalisation