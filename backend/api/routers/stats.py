"""Endpoint de estadísticas de calidad de datos — mide el impacto del pipeline."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from database import get_db
from models.occurrence import Occurrence
from models.taxon import Taxon
from models.location import Location
from models.event import Event

router = APIRouter(prefix="/stats", tags=["Estadísticas"])


@router.get("/calidad")
def calidad_datos(db: Session = Depends(get_db)):
    total = db.query(func.count(Occurrence.occurrence_id)).scalar() or 0
    if total == 0:
        return {"total": 0, "mensaje": "No hay registros cargados aún"}

    con_fecha = (db.query(func.count(Occurrence.occurrence_id))
                 .join(Event, Occurrence.event_id == Event.event_id)
                 .filter(Event.event_date.isnot(None)).scalar() or 0)

    con_coords = (db.query(func.count(Occurrence.occurrence_id))
                  .join(Location, Occurrence.location_id == Location.location_id)
                  .filter(Location.decimal_latitude.isnot(None),
                          Location.decimal_longitude.isnot(None)).scalar() or 0)

    con_taxon = (db.query(func.count(Occurrence.occurrence_id))
                 .join(Taxon, Occurrence.taxon_id == Taxon.taxon_id)
                 .filter(Taxon.scientific_name != "Indeterminado").scalar() or 0)

    con_pais = (db.query(func.count(Occurrence.occurrence_id))
                .join(Location, Occurrence.location_id == Location.location_id)
                .filter(Location.country.isnot(None)).scalar() or 0)

    por_coleccion = (db.query(Occurrence.collection_code, func.count(Occurrence.occurrence_id))
                     .group_by(Occurrence.collection_code).all())

    por_estado = (db.query(Occurrence.occurrence_status, func.count(Occurrence.occurrence_id))
                  .group_by(Occurrence.occurrence_status).all())

    return {
        "total_registros": total,
        "completitud": {
            "con_fecha_evento": _pct(con_fecha, total),
            "con_coordenadas": _pct(con_coords, total),
            "con_nombre_cientifico": _pct(con_taxon, total),
            "con_pais": _pct(con_pais, total),
        },
        "por_coleccion": {c: n for c, n in por_coleccion},
        "por_estado": {e: n for e, n in por_estado},
    }


@router.get("/distribucion-geografica")
def distribucion_geo(db: Session = Depends(get_db)):
    depto_counts = (db.query(Location.state_province, func.count(Location.location_id))
                    .filter(Location.state_province.isnot(None))
                    .group_by(Location.state_province)
                    .order_by(func.count(Location.location_id).desc())
                    .limit(20).all())
    return {"por_departamento": [{"departamento": d, "registros": n} for d, n in depto_counts]}


def _pct(valor: int, total: int) -> dict:
    pct = round(valor / total * 100, 1) if total else 0
    return {"cantidad": valor, "porcentaje": pct}
