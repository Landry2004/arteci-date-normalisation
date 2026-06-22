from fastapi import APIRouter, HTTPException

from src.core.schemas import (
    ColumnsResponse,
    ProcessDateRequest,
    ProcessDateResponse,
)
from src.core.columns_service import get_columns
from src.core.process_service import process_date

router = APIRouter()


# Retourne la liste des colonnes d'un fichier CSV stocké dans MinIO
@router.get("/columns", response_model=ColumnsResponse)
def list_columns(bucket: str, file: str):
    try:
        columns = get_columns(bucket, file)
        return ColumnsResponse(columns=columns)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture des colonnes : {str(e)}",
        )


# Normalise les colonnes date d'un CSV MinIO et retourne un aperçu des 100 premières lignes
@router.post("/processDate", response_model=ProcessDateResponse)
def process_date_endpoint(request: ProcessDateRequest):
    try:
        preview = process_date(
            bucket=request.bucket,
            file=request.file,
            date_columns=request.date_columns,
            date_formats=request.date_formats,
        )
        return ProcessDateResponse(status="success", preview=preview)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement : {str(e)}",
        )