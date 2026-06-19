from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware    # ← AJOUT 1 : l'import
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.core.routes import router
from src.core.observability import setup_tracing, setup_logging

# Configuration de l'observabilité au démarrage
tracer = setup_tracing()
logger = setup_logging()

app = FastAPI(
    title="ARTECI - Date Normalization API",
    description="API haute performance de standardisation des formats de date",
    version="1.0.0",
)

# ── AJOUT 2 : Autoriser les appels depuis un navigateur (CORS) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # autorise toutes les origines
    allow_credentials=True,
    allow_methods=["*"],          # autorise toutes les méthodes (GET, POST...)
    allow_headers=["*"],          # autorise tous les en-têtes
)

# Instrumentation automatique de FastAPI (trace toutes les requêtes HTTP)
FastAPIInstrumentor.instrument_app(app)

# Brancher les routes
app.include_router(router, tags=["dates"])

logger.info("API ARTECI démarrée")


@app.get("/")
def read_root():
    return {
        "message": "ARTECI Date Normalization API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}