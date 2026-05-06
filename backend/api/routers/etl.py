"""Endpoints para disparar el pipeline ETL desde la API."""
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import tempfile
import shutil

from database import get_db
from etl.pipeline import ejecutar_pipeline, procesar_archivo
from etl.mapper import generar_reporte_mapeo
from etl.loader import cargar_archivo

router = APIRouter(prefix="/etl", tags=["ETL"])


@router.post("/cargar-directorio")
def cargar_directorio(db: Session = Depends(get_db)):
    """Procesa todos los archivos del directorio muestras/."""
    resultados = ejecutar_pipeline(db)
    return {
        "archivos_procesados": len(resultados),
        "resultados": [
            {
                "archivo": r.archivo,
                "total_filas": r.total_filas,
                "insertados": r.insertados,
                "actualizados": r.actualizados,
                "omitidos": r.omitidos,
                "errores": r.errores[:5],
                "mapeo": r.reporte_mapeo,
            }
            for r in resultados
        ],
    }


@router.post("/cargar-archivo")
async def cargar_archivo_upload(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sube y procesa un archivo Excel/CSV."""
    sufijo = Path(archivo.filename).suffix.lower()
    if sufijo not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx, .xls o .csv")

    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        shutil.copyfileobj(archivo.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        resultado = procesar_archivo(tmp_path, db)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "archivo": archivo.filename,
        "total_filas": resultado.total_filas,
        "insertados": resultado.insertados,
        "actualizados": resultado.actualizados,
        "omitidos": resultado.omitidos,
        "errores": resultado.errores[:10],
        "mapeo": resultado.reporte_mapeo,
    }


@router.post("/previsualizar-mapeo")
async def previsualizar_mapeo(archivo: UploadFile = File(...)):
    """Retorna el mapeo de columnas sin cargar datos."""
    sufijo = Path(archivo.filename).suffix.lower()
    if sufijo not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(status_code=400, detail="Formato no soportado")

    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        shutil.copyfileobj(archivo.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        df = cargar_archivo(tmp_path)
        reporte = generar_reporte_mapeo(list(df.columns))
    finally:
        tmp_path.unlink(missing_ok=True)

    return reporte
