from pydantic import BaseModel


# ─── GET /columns ──────────────────────────────────────
class ColumnsResponse(BaseModel):
    columns: list[str]


# ─── POST /processDate ─────────────────────────────────
class ProcessDateRequest(BaseModel):
    bucket: str
    file: str
    date_columns: list[str]
    date_formats: list[str]


class ProcessDateResponse(BaseModel):
    status: str
    preview: list[dict]