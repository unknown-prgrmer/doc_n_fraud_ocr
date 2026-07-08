- [Test Technique : Python Developer](#test-technique--data-engineer)
  - [Project Architecture & Philosophy](#project-architecture--philosophy)
  - [Disclaimer](#disclaimer)
  - [Introduction](#introduction)
  - [Contexte du test](#contexte-du-test)
  - [Avant de commencer](#avant-de-commencer)
    - [Bonnes pratiques](#bonnes-pratiques)
    - [Quelques conseils pour bien démarrer](#quelques-conseils-pour-bien-démarrer)
  - [Objectifs](#objectifs)
    - [Étapes à réaliser](#étapes-à-réaliser)
    - [Consignes de base à respecter impérativement](#consignes-de-base-à-respecter-impérativement)
    - [Collecte et stockage des données](#collecte-et-stockage-des-données)
    - [Monitoring de la qualité des prédictions](#monitoring-de-la-qualité-des-prédictions)
  - [Livrables](#livrables)
  - [Durée estimée](#durée-estimée)
  - [Exécution](#exécution)

# Test Technique : Python Developer

## Project Architecture & Philosophy

### Overview

This project implements a **data collection and quality monitoring pipeline** for OCR (Optical Character Recognition) predictions. It processes images from URLs, stores them in MinIO, persists metadata in MongoDB, and exposes Prometheus metrics for monitoring prediction quality via Grafana dashboards.

The architecture follows **Ports/Adapters Architecture** principles with clear separation of concerns across layers, enabling testability, maintainability, and easy infrastructure swapping.

### AI Assistance & Transparency

**When AI was used:**
- Project structure design and layer separation strategy
- Port/interface definitions for dependency injection
- Prometheus metrics setup and patterns
- Docker configuration and infrastructure-as-code
- Test patterns and test double implementations
- Documentation and code comments

**How AI was used:**
- Generated boilerplate code for infrastructure adapters (MinIO client, MongoDB persistence, Prometheus metrics)
- Provided patterns for dependency injection containers and factory methods
- Validated architectural decisions against Ports/Adapters principles
- Reviewed and refined testing strategies for in-memory implementations

**Critical validation performed:**
- All generated code was manually tested against the API
- Infrastructure implementations verified with actual services (MinIO, MongoDB, Prometheus)
- Tested multiple scenarios: happy path, error handling, edge cases
- Validated that dependency injection enables seamless switching between implementations
- Confirmed unit tests pass without external services running

### Architecture Layers & Design Patterns

#### 1. **Entities** (`app/entities/`)
**Purpose:** Domain models representing core business concepts
**Philosophy:** Pure, immutable data structures with business validation rules
**Examples:** `Prediction`, `PredictionMetadata`, `PredictionRecord`

- Use Pydantic for validation enforcement
- Frozen models prevent accidental mutations
- No external dependencies; purely business logic
- These are shared across all layers and represent your ubiquitous language

#### 2. **Ports** (`app/ports/`)
**Purpose:** Abstract interfaces defining contracts for external dependencies
**Philosophy:** Inversion of Control (IoC) - business logic never depends on concrete implementations
**Examples:** `OCRService`, `ImageRepository`, `MetadataRepository`

- Define what operations are needed (abstract methods)
- Technology-agnostic interfaces (ABC - Abstract Base Classes)
- Enable switching implementations without changing business logic
- Critical for testing: in-memory stubs replace real services

#### 3. **Usecases** (`app/usecases/`)
**Purpose:** Application business rules orchestrating core workflows
**Philosophy:** Pure logic independent of delivery mechanism (API, CLI, etc.)
**Examples:** `PredictUsecase` - orchestrates OCR prediction, image storage, metadata persistence

- Depends only on ports (interfaces), never concrete implementations
- Contains the core prediction logic uncontaminated by infrastructure
- Dependency Injection through constructor enables testability
- Metrics emission happens here - business logic is observable

**Why DI/IoC here?**
The usecase receives dependencies (OCR service, repositories) as constructor arguments. This means:
- Unit tests can inject in-memory stubs instead of real services
- Integration tests can use different repository implementations
- Production can use MinIO/MongoDB while tests use in-memory equivalents
- Logic never changes; only implementations swap

#### 4. **Infra** (`app/infra/`)
**Purpose:** Concrete implementations of ports for specific technologies
**Philosophy:** Pluggable adapters that handle external concerns

**Subdirectories:**
- `fastapi/` - HTTP API layer (routers, schemas, exception handling)
- `repositories/` - Implementations: MinIO for images, MongoDB for metadata, in-memory for testing
- `services/` - Concrete implementations: HTTP-based image downloader, Prometheus metrics exporter, OCR service stub
- `repositories/inmemory/` - In-memory test doubles allowing fast, isolated tests without external services

**Why in-memory implementations?**
- Tests run fast without network I/O or database overhead
- Tests pass without Docker services running (CI/CD environments)
- Deterministic and reproducible test results
- No test data cleanup needed between runs
- Enables test-driven development without infrastructure setup friction

#### 5. **Services** (`app/services/`)
**Purpose:** Domain services orchestrating business logic across entities
**Philosophy:** Stateless operations on entities; bridge between usecases and complex calculations

#### 6. **Repositories** (within `infra/repositories/`)
**Purpose:** Data access abstraction implementing persistence ports
**Philosophy:** Transform domain entities to/from storage format

- `minio_image_repository.py` - S3-compatible image storage
- `mongodb_metadata_repository.py` - NoSQL metadata persistence
- `im_image_repository.py` - In-memory stub for testing
- `im_metadata_repository.py` - In-memory stub for testing

### Dependency Flow

```
HTTP Router (FastAPI)
    ↓
PredictUsecase (Business Logic)
    ├─→ OCRService (port)
    ├─→ ImageRepository (port)
    └─→ MetadataRepository (port)
            ↓
        Concrete implementations:
        • minio_image_repository.py
        • mongodb_metadata_repository.py
        • stub_ocr_service.py (in-memory)
```

The flow is **unidirectional inward**: outer layers depend on inner layers, never the reverse.

### Key Testing Benefits of This Structure

1. **Unit tests inject in-memory stubs** - no external service dependencies
2. **Integration tests swap implementations** - same code tests against different backends
3. **Fast feedback loop** - tests run in milliseconds, not seconds
4. **Isolation** - test failures pinpoint exact component, not infrastructure
5. **Reproducibility** - no race conditions, no test order dependencies

### Prometheus Metrics & Monitoring

Metrics are emitted from the usecase layer (business logic is observable):
- Prediction counts and confidence scores
- Low-confidence alert thresholds
- Request latency and throughput

Configuration:
- `provisioning/prometheus/` - scrape targets and alert rules
- `provisioning/grafana/` - dashboards and data sources (provisioned automatically on startup)

---

## Disclaimer

Le test est conçu pour évaluer votre approche et votre capacité à résoudre des problèmes de manière pratique. Nous comprenons que le temps et les ressources sont limités, et il est normal de ne pas pouvoir compléter chaque partie du test. Ce qui nous intéresse avant tout, c'est votre raisonnement, la façon dont vous abordez les problèmes et les choix que vous faites pour résoudre les différentes étapes.

Nous ne recherchons pas de solution parfaite, ni à l'état de l'art, mais plutôt une solution fonctionnelle, claire et bien documentée. Il est important d’expliquer vos choix dans un fichier dédié ou directement dans les commentaires du code. Nous préférons un code simple, mais qui fonctionne, plutôt qu'un code plus complexe, mais difficile à exécuter.

N’hésitez pas à simplifier certaines parties du test si nécessaire (par exemple, gérer uniquement des fichiers spécifiques ou vous concentrer sur une approche plus rapide), mais veillez à bien documenter vos décisions.

### Utilisation d'outils d'assistance par IA

L'utilisation d'outils d'assistance par intelligence artificielle n'est pas interdite pour la réalisation de ce test. Si vous choisissez d'y avoir recours, nous accordons une grande importance à la transparence de cette démarche.

Lors de l'évaluation de votre rendu, nous serons particulièrement attentifs à la façon dont vous détaillez :
- **Votre usage :** pour quelles tâches ou étapes avez-vous sollicité l'IA ?
- **Votre méthode de travail :** comment avez-vous interagi avec l'outil ?
- **Votre esprit critique :** comment vous êtes-vous assuré de la véracité et du bien-fondé du code et des solutions proposées par l'IA ?

L'objectif principal reste d'évaluer votre propre démarche d'ingénierie et votre capacité à valider techniquement les solutions implémentées.

Bonne chance, et surtout, amusez-vous avec ce test !

---

## Introduction

Chez QuickSign, nous traitons des dizaines de milliers de documents tous les mois. L'équipe Doc&Fraud a notamment pour rôle de créer des algorithmes permettant de classifier et de lire ces documents. Ces différents algorithmes sont ensuite appelés via une API.

Ce test technique vise à évaluer votre capacité à :

- Créer une pipeline d'ingestion de données complète.
  - Récupération depuis une URL,
  - Stockage de la donnée, de manière sécurisée,
  - Indexation de la donnée dans une base de données,
- Assurer la qualité de votre code via des tests et de la documentation.
- Maintenir la conteneurisation de la solution à l'aide de Docker.

---

## Contexte du test

Les data scientists sont en charge d’une API FastAPI qui expose un modèle d'océrisation à partir d'une image d'une ligne de texte. Dans le scénario de ce test, le modèle en production est jugé **très peu performant** d'un point de vue produit.
Votre mission est de mettre en place une **pipeline de collecte de données** pour permettre aux data scientists d’entraîner un nouveau modèle, tout en assurant un **monitoring de la qualité des prédictions** afin d'avoir des chiffres pour nourir les discussions avec les équipes produit. Vous ne disposez d’aucune donnée d’entraînement pour le moment.

Ce qui est fourni :
- L’API FastAPI est déjà en place et retourne des prédictions de texte à partir d’une image d'une ligne de texte.
- Le modèle utilisé est un modèle pré-entraîné, mais ses performances sont jugées mauvaises.
- Vous avez accès à :
  - **MinIO** (compatible S3) pour stocker les images
  - **MongoDB** pour stocker les métadonnées et les résultats
  - **Prometheus** et **Grafana** pour le monitoring

Ce qui est à faire :
- Vous devez trouver des données (annotées ou non) et les stocker pour qu'elles puissent être annotées et utilisées par les data scientists pour ré-entraîner un modèle.

Voici des exemples de sources d'images à utiliser :


| Source                     | Description                        | Exemple d’URL                                                                 |
|----------------------------|------------------------------------|-------------------------------------------------------------------------------|
| IAM Handwriting Database | Écriture manuscrite réelle, contenant le texte `industrie`        | https://fki.tic.heia-fr.ch/static/img/a01-122-02-00.jpg                      |
| Scanned printed text     | Texte dactylographié, contenant le texte `Wikipedia`               | https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvc9YzVQCGKRAu7LMZObym4YElk59PqVWlHg&s |

---


## Avant de commencer

### Bonnes pratiques

L'ensemble de nos librairies et nos services sont développés avec l'outil [uv](https://docs.astral.sh/uv/). Cela nous permet de les versionner, de développer plusieurs services / librairies sur la même machine en utilisant des environnements virtuels et de gérer les dépendances de nos services / librairies en fixant les versions des packages dont ils dépendent. L'utilisation de uv dans le cadre de ce test technique est donc primordiale et nous permet de tester le code reçu en quelques lignes. Un environnement à jour est indispensable afin de nous permettre de tester le code.

Le script `lint_module.sh` permet d'automatiser l'application de `ruff` (pour formater le code et respecter les normes définies) et `ty` (pour la gestion du typage).

Nous accordons par ailleurs une forte importance à la réalisation de tests unitaires, et au coverage de ceux-ci. Pour les lancer et avoir un rapport de coverage, utilisez le script `run_tests.sh`

Nous vous conseillons, avant même de poursuivre, de nous assurer que vous avez sur votre machine :

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [docker](https://docs.docker.com/engine/install/)

et que vous êtes en capacité de lancer les commandes dont vous aurez besoin tout au long du test

```
uv sync --all-extras
./lint_module.sh
./run_tests.sh
docker compose up --build
```

Nous accorderons beaucoup d'importance aux respects des consignes et à la méthodologie scientifique, assez peu, voire aucune importance aux résultats statistiques.

### Quelques conseils pour bien démarrer

Le service d'océrisation (OCR) a été stubbed pour éviter de longs téléchargements et accélérer l'installation de votre environnement. Il retourne de manière aléatoire des prédictions textuelles et des scores de confiance, ce qui vous permet de tester vos pipelines et vos dashboards de monitoring dans les mêmes conditions de manière instantanée.

Pour commencer, nous vous conseillons de lancer les services tels quel, afin de vous familiariser avec ceux ci.
* Testez l'API fournie, en examinant ce qu'il y a en sortie de la route predict sur un exemple
* Connectez vous à grafana
  * login et mot de passe par défaut : `admin`/`admin` puis
  * Configurez les Connections à prometheus (`Connections` -> `Add new connection` -> `prometheus` -> `Add new data source` et mettre l'adresse du serveur `http://prometheus:9090`)
  * Créez ensuite votre premier dashboard : `Dashboards` -> `Create Dashboards` -> `Import Dashboard` -> vous pouvez utiliser le grafana ID `193` pour ajouter [ce dashboard](https://grafana.com/grafana/dashboards/193-docker-monitoring/)). Vous aurez là des informations de base de vos services (CPU, mémoire, réseau)
  * A noter que pour le rendu final, la connexion Grafana/Prometheus et les dashboards Grafana devront être dans des fichiers de configuration
* Connectez vous à minio
  * login et mot de passe par défaut : `minioadmin`/`minioadmin`
* Connectez vous à la mongoDB en utilisant par exemple [mongodb compass](https://www.mongodb.com/products/tools/compass), en utilisant l'adresse `mongodb://localhost:27017/`

---

## Objectifs

### Étapes à réaliser

1. **Récupération de la donnée** : Utilisez des images issues de jeux de données publics ou générez-les si nécessaire.
2. **Ingestion de la donnée** : Implémentez un système qui permet d'ingérer une image à partir d'une URL. L'implémentation de ce système est laissé libre, ça peut être implémenté directement dans le service donné, dans un autre service ou tout autre moyen, tant qu'il utilise le service pour récupérer les prédictions du modèle.
3. **Mise en place des métriques** : Implémentez les métriques et le(s) dashboard(s) associé(s).
4. **Conteneurisation** : Modifiez le Dockerfile si nécessaire pour inclure vos dépendances. Vérifiez que le service fonctionne avec `docker compose up --build`.
5. **Testing** : Vérifier que tout est fonctionnel à l'aide de tests.

### Consignes de base à respecter impérativement

1. Les quatre actions suivantes sont executées sans erreur :

```
uv sync --all-extras
./lint_module.sh
./run_tests.sh
docker compose up --build
```

Note: Les tests unitaires doivent passer sans erreur (hors coverage) même lorsque les services ne sont pas lancés.

2. Des tests sont implémentés.

3. Le service FastAPI est utilisé, avec des métriques ajoutées.

4. Docker est utilisé pour conteneuriser votre application.

5. Les fichiers de configuration de Grafana et Prometheus sont implémentés.

6. Votre `pyproject.toml` doit être à jour et fonctionnel sur un système Linux (Debian / Ubuntu).


### Collecte et stockage des données

Mettre en place une **pipeline de collecte de données** à partir des requêtes reçues par l’API :

- Télécharger l’image à partir d’une **URL**
- Sauvegarder l’image dans **MinIO**
- Sauvegarder les métadonnées associées dans **MongoDB** :
  - Le timestamp
  - L'annotation si disponible
  - La prédiction du modèle associée à l'image
  - Le chemin de l’image dans MinIO
  - l'URL source de l’image pour des raisons réglementaires



---

### Monitoring de la qualité des prédictions

Des exemples de dashboards sont disponibles sur le port 9004.


Mettre en place un système de **métriques Prometheus** exposées par l’API :

- Score moyen des prédictions
- Nombre de prédictions par minute
- Nombre de scores < seuil (ex: 0.5)

Créer un **dashboard Grafana** avec au moins :

- Un graphique de l’évolution du score moyen dans le temps
- Une alerte si le score moyen passe sous un seuil critique

---


## Livrables

Un dossier contenant :

- Votre code source dans le dossier `app/`.
- Le nécéssaire pour générer un environnement virtuel faisant tourner l'application à l'aide de uv.
- Vos fichiers de configuration Docker.
- Des tests unitaires vérifiant les fonctionnalités de votre API.

---

## Durée estimée

Le test ne devrait pas prendre plus d'une demi-journée.

---

## Exécution

Ce setup a été pensé pour une machine GNU/Linux (Ubuntu par exemple). Si vous n'avez pas accès directement à cet OS, nous vous conseillons d'utiliser une VM ou Docker.

Les fichiers `Dockerfile` et `docker-compose.yml` permettent de lancer :

- le web service sur le port `8080`
- le grafana sur port `3000`
- le prometheus sur port `9000`
- le mongo sur le port `27017`
- le minio :
  - API sur le port `9002`
  - console sur le port `9003`

via la commande :

```
docker compose up --build
```
