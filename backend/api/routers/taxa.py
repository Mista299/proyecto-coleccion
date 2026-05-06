from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.taxon import Taxon

router = APIRouter(prefix="/taxa", tags=["Taxa"])


@router.get("/")
def listar(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    nombre: str | None = None,
    familia: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Taxon)
    if nombre:
        q = q.filter(Taxon.scientific_name.ilike(f"%{nombre}%"))
    if familia:
        q = q.filter(Taxon.family.ilike(f"%{familia}%"))
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [_ser(t) for t in items],
    }


@router.get("/resumen")
def resumen_taxonomico(db: Session = Depends(get_db)):
    familias = (db.query(Taxon.family, func.count(Taxon.taxon_id))
                .filter(Taxon.family.isnot(None))
                .group_by(Taxon.family)
                .order_by(func.count(Taxon.taxon_id).desc())
                .all())
    ordenes = (db.query(Taxon.order, func.count(Taxon.taxon_id))
               .filter(Taxon.order.isnot(None))
               .group_by(Taxon.order)
               .order_by(func.count(Taxon.taxon_id).desc())
               .all())
    return {
        "total_taxones": db.query(func.count(Taxon.taxon_id)).scalar(),
        "por_familia": [{"familia": f, "count": c} for f, c in familias[:20]],
        "por_orden": [{"orden": o, "count": c} for o, c in ordenes[:10]],
    }


def _ser(t: Taxon) -> dict:
    return {
        "taxonID": t.taxon_id,
        "scientificName": t.scientific_name,
        "taxonRank": t.taxon_rank,
        "kingdom": t.kingdom,
        "family": t.family,
        "genus": t.genus,
    }
