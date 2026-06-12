from fastapi import FastAPI

from src.core.routes import router

app = FastAPI(
    title="ARTECI - Date Normalization API",
    description="API haute performance de standardisation des formats de date",
    version="1.0.0",
)

# Brancher les routes de l'application
app.include_router(router, tags=["dates"])


@app.get("/")
def read_root():
    return {
        "message": "ARTECI Date Normalization API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}