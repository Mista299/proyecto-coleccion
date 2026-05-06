"""
Pipeline ETL principal.
Lee un archivo Excel/CSV → mapea columnas → normaliza → carga en PostgreSQL (upsert).
"""
import uuid
import hashlib
from pathlib import Path
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import INSTITUTION_CODE
from etl.loader import cargar_archivo, inferir_collection_code
from etl.mapper import mapear_columnas
from etl.normalizer import (
    normalizar_fecha, parsear_fecha_texto,
    normalizar_coordenada,
    construir_scientific_name, normalizar_taxon_rank,
    normalizar_occurrence_status, normalizar_disposition,
)
from models.taxon import Taxon
from models.event import Event
from models.location import Location
from models.occurrence import Occurrence
from models.identification import Identification


def _upsert(db: Session, model, data: dict, pk: str = None):
    """Upsert seguro usando INSERT ON CONFLICT para PostgreSQL."""
    pk_col = pk or list(model.__table__.primary_key.columns.keys())[0]
    stmt = (
        pg_insert(model.__table__)
        .values(**data)
        .on_conflict_do_update(index_elements=[pk_col], set_=data)
    )
    db.execute(stmt)


@dataclass
class ResultadoPipeline:
    archivo: str
    total_filas: int = 0
    insertados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = field(default_factory=list)
    reporte_mapeo: dict = field(default_factory=dict)


def _to_int(valor) -> int | None:
    try:
        return int(float(str(valor))) if valor and str(valor).strip() not in ("", "nan") else None
    except (ValueError, TypeError):
        return None


def _uid(*partes) -> str:
    """Genera UUID determinista desde partes concatenadas."""
    texto = "|".join(str(p) for p in partes)
    return str(uuid.UUID(hashlib.md5(texto.encode()).hexdigest()))


def _val(row: pd.Series, *claves) -> str | None:
    """Retorna el primer valor no nulo de las claves dadas en la fila."""
    for k in claves:
        if k in row.index and pd.notna(row[k]) and str(row[k]).strip() not in ("", "nan"):
            return str(row[k]).strip()
    return None


def _col(mapeo: dict[str, str | None], dwc_term: str) -> list[str]:
    """Retorna lista de columnas reales que mapean a un término DwC."""
    return [col for col, term in mapeo.items() if term == dwc_term]


def procesar_archivo(path: Path, db: Session) -> ResultadoPipeline:
    path = Path(path)
    resultado = ResultadoPipeline(archivo=path.name)
    collection_code = inferir_collection_code(path)

    try:
        df = cargar_archivo(path)
    except Exception as e:
        resultado.errores.append(f"Error leyendo archivo: {e}")
        return resultado

    resultado.total_filas = len(df)
    mapeo = mapear_columnas(list(df.columns))
    resultado.reporte_mapeo = {
        "total_columnas": len(df.columns),
        "mapeadas": sum(1 for v in mapeo.values() if v),
        "sin_mapear": [k for k, v in mapeo.items() if not v],
    }

    # Helpers para acceder columnas por término DwC
    def get_cols(term: str) -> list[str]:
        return _col(mapeo, term)

    def fila_val(row: pd.Series, term: str, *fallback_terms) -> str | None:
        cols = get_cols(term)
        for ft in fallback_terms:
            cols += get_cols(ft)
        return _val(row, *cols)

    for idx, row in df.iterrows():
        try:
            # ── occurrenceID ──────────────────────────────────────────────────
            cat_raw = fila_val(row, "occurrenceID", "catalogNumber")
            if not cat_raw:
                resultado.omitidos += 1
                continue
            occurrence_id = f"{INSTITUTION_CODE}:{collection_code}:{cat_raw}"

            # ── Taxon ─────────────────────────────────────────────────────────
            genero_cols = [c for c in df.columns if "genero" in c.lower() or "genus" in c.lower()]
            epiteto_cols = [c for c in df.columns if "epiteto" in c.lower() or "specific" in c.lower()]
            det_cols = [c for c in df.columns if "determinacion" in c.lower()]

            genero = _val(row, *genero_cols)
            epiteto = _val(row, *epiteto_cols)
            determinacion = _val(row, *det_cols)

            sci_name = construir_scientific_name(genero, epiteto, determinacion)
            taxon_rank = normalizar_taxon_rank(genero, epiteto)

            # Campos taxonómicos adicionales
            reino_cols = [c for c in df.columns if "reino" in c.lower() or c.lower().startswith("reino")]
            filo_cols = [c for c in df.columns if "filo" in c.lower() or "phyl" in c.lower()]
            clase_cols = [c for c in df.columns if "clase" in c.lower() or "class" in c.lower()]
            orden_cols = [c for c in df.columns if "orden" in c.lower() or "order" in c.lower()]
            familia_cols = [c for c in df.columns if "familia" in c.lower() or "family" in c.lower()]

            taxon_id = _uid("taxon", sci_name or "indet")
            taxon_data = {
                "taxon_id": taxon_id,
                "scientific_name": sci_name or "Indeterminado",
                "taxon_rank": taxon_rank,
                "kingdom": _val(row, *reino_cols),
                "phylum": _val(row, *filo_cols),
                "class": _val(row, *clase_cols),
                "order": _val(row, *orden_cols),
                "family": _val(row, *familia_cols),
                "genus": genero,
                "specific_epithet": epiteto,
            }
            _upsert(db, Taxon, taxon_data, "taxon_id")

            # ── Event ─────────────────────────────────────────────────────────
            dia_cols = [c for c in df.columns if "dia_colecta" in c.lower()]
            mes_cols = [c for c in df.columns if "mes_colecta" in c.lower()]
            ano_cols = [c for c in df.columns if "ano_colecta" in c.lower()]

            dia = _val(row, *dia_cols)
            mes = _val(row, *mes_cols)
            ano = _val(row, *ano_cols)
            event_date = normalizar_fecha(dia, mes, ano)

            # Fallback: columna de fecha directa
            if not event_date:
                fecha_raw = fila_val(row, "eventDate")
                event_date = parsear_fecha_texto(fecha_raw)

            event_id = _uid("event", event_date or "unknown", occurrence_id)
            habitat_cols = [c for c in df.columns if "habitat" in c.lower()]
            metodo_cols = [c for c in df.columns if "metodo_colecta" in c.lower()]
            event_data = {
                "event_id": event_id,
                "event_date": event_date,
                "year": _to_int(ano),
                "month": _to_int(mes),
                "day": _to_int(dia),
                "habitat": _val(row, *habitat_cols),
                "sampling_protocol": _val(row, *metodo_cols),
            }
            _upsert(db, Event, event_data, "event_id")

            # ── Location ──────────────────────────────────────────────────────
            lat_cols = [c for c in df.columns if "latitud" in c.lower() or c.lower() == "lat"]
            lon_cols = [c for c in df.columns if "longitud" in c.lower() or c.lower() == "lon"]
            pais_cols = [c for c in df.columns if "pais" in c.lower()]
            depto_cols = [c for c in df.columns if "departamento" in c.lower()]
            mpio_cols = [c for c in df.columns if "municipio" in c.lower()]
            loc_cols = [c for c in df.columns if "localidad" in c.lower()]
            elev_cols = [c for c in df.columns if "elev_minima" in c.lower()]

            lat = normalizar_coordenada(_val(row, *lat_cols), "lat")
            lon = normalizar_coordenada(_val(row, *lon_cols), "lon")

            location_id = _uid("location", _val(row, *pais_cols) or "",
                               _val(row, *depto_cols) or "", _val(row, *mpio_cols) or "",
                               str(lat), str(lon))
            location_data = {
                "location_id": location_id,
                "event_id": event_id,
                "country": _val(row, *pais_cols),
                "state_province": _val(row, *depto_cols),
                "county": _val(row, *mpio_cols),
                "locality": _val(row, *loc_cols),
                "decimal_latitude": lat,
                "decimal_longitude": lon,
                "geodetic_datum": "WGS84",
                "minimum_elevation": float(_val(row, *elev_cols)) if _val(row, *elev_cols) else None,
            }
            _upsert(db, Location, location_data, "location_id")

            # ── Occurrence ────────────────────────────────────────────────────
            estado_cols = [c for c in df.columns if c.lower().startswith("estado_")]
            prep_cols = [c for c in df.columns if "preparacion" in c.lower()]
            sexo_cols = [c for c in df.columns if "sexo" in c.lower()]
            num_ind_cols = [c for c in df.columns if "numero_" in c.lower() and "individuo" in c.lower()]
            colector_n = [c for c in df.columns if "nombre_colector" in c.lower()]
            colector_a = [c for c in df.columns if "apellidos_colector" in c.lower()]
            campo_cols = [c for c in df.columns if "numero_campo" in c.lower()]

            estado_raw = _val(row, *estado_cols)
            num_ind_raw = _val(row, *num_ind_cols)

            colector_parts = [p for p in [_val(row, *colector_n), _val(row, *colector_a)] if p]
            colector = " ".join(colector_parts) if colector_parts else None

            occurrence_data = {
                "occurrence_id": occurrence_id,
                "basis_of_record": "PreservedSpecimen",
                "institution_code": INSTITUTION_CODE,
                "collection_code": collection_code,
                "catalog_number": cat_raw,
                "occurrence_status": normalizar_occurrence_status(estado_raw),
                "disposition": normalizar_disposition(estado_raw),
                "preparations": _val(row, *prep_cols),
                "sex": _val(row, *sexo_cols),
                "individual_count": int(float(num_ind_raw)) if num_ind_raw else None,
                "recorded_by": colector,
                "field_number": _val(row, *campo_cols),
                "source_file": path.name,
                "event_id": event_id,
                "taxon_id": taxon_id,
                "location_id": location_id,
            }
            existing = db.get(Occurrence, occurrence_id)
            if existing:
                resultado.actualizados += 1
            else:
                resultado.insertados += 1
            _upsert(db, Occurrence, occurrence_data, "occurrence_id")

            # ── Identification ────────────────────────────────────────────────
            id_por_cols = [c for c in df.columns if "identificado_por" in c.lower()]
            identificado_por = _val(row, *id_por_cols)
            if identificado_por or sci_name:
                ident_id = _uid("ident", occurrence_id, identificado_por or "")
                ident_data = {
                    "identification_id": ident_id,
                    "occurrence_id": occurrence_id,
                    "taxon_id": taxon_id,
                    "identified_by": identificado_por,
                    "verification_status": "unverified",
                }
                _upsert(db, Identification, ident_data, "identification_id")

        except Exception as e:
            resultado.errores.append(f"Fila {idx}: {e}")

    db.commit()
    return resultado


def ejecutar_pipeline(db: Session, directorio: Path | None = None) -> list[ResultadoPipeline]:
    """Procesa todos los archivos Excel/CSV de un directorio."""
    from config import MUESTRAS_DIR
    dir_path = Path(directorio) if directorio else MUESTRAS_DIR
    archivos = list(dir_path.glob("*.xlsx")) + list(dir_path.glob("*.xls")) + list(dir_path.glob("*.csv"))
    return [procesar_archivo(a, db) for a in sorted(archivos)]
