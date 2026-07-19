from fastapi import FastAPI

from app import config
from app.models import Category, ProcessedRecord
from app.storage import Storage
from app.sync_service import SyncResult, run_sync

app = FastAPI(title="Gmail Classifier Agent")

# endpoint para obtener las categorías de clasificación
@app.get("/categories")
def get_categories() -> list[Category]:
    return config.load_categories()


# endpoint para sincronizar los correos electrónicos y clasificarlos
@app.post("/sync")
def sync() -> SyncResult:
    return run_sync()


# endpoint para obtener los registros de correos electrónicos procesados
@app.get("/processed")
def get_processed(limit: int = 50) -> list[ProcessedRecord]:
    return Storage().list_recent(limit)
