from fastapi import APIRouter, HTTPException

from src.core.schemas import ColumnsResponse
from src.core.columns_service import get_columns

router = APIRouter()


@router.get("/columns", response_model=ColumnsResponse)
def list_columns(bucket: str, file: str):
    """
    Retourne la liste des colonnes d'un fichier stocké dans MinIO.

    Paramètres :
    - bucket : nom du bucket MinIO contenant le fichier
    - file : chemin du fichier dans le bucket
    """
    try:
        columns = get_columns(bucket, file)
        return ColumnsResponse(columns=columns)

    except FileNotFoundError as e:
        # Fichier introuvable → erreur 404 explicite
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # Toute autre erreur → 500 avec message clair
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture des colonnes : {str(e)}",
        )