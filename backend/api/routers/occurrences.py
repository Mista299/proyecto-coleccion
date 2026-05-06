from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from database import get_db
from models.occurrence import Occurrence
from models.taxon import Taxon
from models.location import Location
from models.event import Event

router = APIRouter(prefix="/occurrences", tags=["Occurrences"])


@router.get("/")
def listar(
    skip: int = 0,
    limit: int = Query(default=50, le=500),
    collection_code: str | None = None,
    taxon: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Occurrence)
    if collection_code:
        q = q.filter(Occurrence.collection_code == collection_code)
    if taxon:
        q = q.join(Taxon).filter(Taxon.scientific_name.ilike(f"%{taxon}%"))
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [_serializar(o) for o in items],
    }


@router.get("/{occurrence_id}")
def obtener(occurrence_id: str, db: Session = Depends(get_db)):
    o = db.get(Occurrence, occurrence_id)
    if not o:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return _serializar(o, detallado=True)


@router.delete("/{occurrence_id}", status_code=204)
def eliminar(occurrence_id: str, db: Session = Depends(get_db)):
    o = db.get(Occurrence, occurrence_id)
    if not o:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(o)
    db.commit()


def _serializar(o: Occurrence, detallado: bool = False) -> dict:
    base = {
        "occurrenceID": o.occurrence_id,
        "catalogNumber": o.catalog_number,
        "collectionCode": o.collection_code,
        "basisOfRecord": o.basis_of_record,
        "occurrenceStatus": o.occurrence_status,
        "disposition": o.disposition,
        "sex": o.sex,
        "recordedBy": o.recorded_by,
        "sourceFile": o.source_file,
    }
    if detallado:
        if o.taxon:
            base["taxon"] = {
                "scientificName": o.taxon.scientific_name,
                "taxonRank": o.taxon.taxon_rank,
                "family": o.taxon.family,
                "genus": o.taxon.genus,
            }
        if o.event:
            base["event"] = {
                "eventDate": o.event.event_date,
                "habitat": o.event.habitat,
            }
        if o.location:
            base["location"] = {
                "country": o.location.country,
                "stateProvince": o.location.state_province,
                "county": o.location.county,
                "locality": o.location.locality,
                "decimalLatitude": float(o.location.decimal_latitude) if o.location.decimal_latitude else None,
                "decimalLongitude": float(o.location.decimal_longitude) if o.location.decimal_longitude else None,
            }
    return base
