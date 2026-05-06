"""
Normaliza valores de campos DwC:
- Fechas → ISO 8601 (YYYY-MM-DD)
- Coordenadas → decimal WGS84
- Nombres taxonómicos → formato Género especie
- occurrenceStatus / disposition → vocabulario controlado DwC
"""
import re
import math
import pandas as pd
from typing import Any


# ── Fechas ────────────────────────────────────────────────────────────────────

def normalizar_fecha(dia: Any, mes: Any, ano: Any) -> str | None:
    """Combina campos día/mes/año separados en ISO 8601."""
    try:
        d = int(float(dia)) if pd.notna(dia) and str(dia).strip() not in ("", "nan") else None
        m = int(float(mes)) if pd.notna(mes) and str(mes).strip() not in ("", "nan") else None
        a = int(float(ano)) if pd.notna(ano) and str(ano).strip() not in ("", "nan") else None
    except (ValueError, TypeError):
        return None

    if a is None:
        return None
    if m is None:
        return str(a)
    if d is None:
        return f"{a:04d}-{m:02d}"
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return None
    return f"{a:04d}-{m:02d}-{d:02d}"


def parsear_fecha_texto(texto: Any) -> str | None:
    """Intenta parsear una fecha de texto con múltiples formatos."""
    if pd.isna(texto) or str(texto).strip() in ("", "nan"):
        return None
    t = str(texto).strip()
    # Ya en ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", t):
        return t
    # dd/mm/yyyy o dd-mm-yyyy
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    # yyyy/mm/dd
    m = re.match(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # Solo año
    m = re.match(r"^(\d{4})$", t)
    if m:
        return m.group(1)
    return None


# ── Coordenadas ───────────────────────────────────────────────────────────────

def _dms_a_decimal(texto: str) -> float | None:
    """Convierte DMS (ej. '6°3'26.8"N') a decimal."""
    patron = r"""(\d+)[°d]\s*(\d+)['m']\s*([\d.]+)[\"s]?\s*([NSEW]?)"""
    m = re.search(patron, texto, re.IGNORECASE)
    if not m:
        return None
    grados, minutos, segundos, hemisferio = m.groups()
    decimal = float(grados) + float(minutos) / 60 + float(segundos) / 3600
    if hemisferio.upper() in ("S", "W"):
        decimal = -decimal
    return round(decimal, 7)


def normalizar_coordenada(valor: Any, tipo: str = "lat") -> float | None:
    """Normaliza latitud o longitud a decimal. tipo: 'lat' o 'lon'."""
    if pd.isna(valor) or str(valor).strip() in ("", "nan"):
        return None
    try:
        dec = float(str(valor).replace(",", "."))
    except ValueError:
        dec = _dms_a_decimal(str(valor))
    if dec is None or math.isnan(dec):
        return None
    if tipo == "lat" and not (-90 <= dec <= 90):
        return None
    if tipo == "lon" and not (-180 <= dec <= 180):
        return None
    return round(dec, 7)


# ── Taxonomía ─────────────────────────────────────────────────────────────────

def construir_scientific_name(genero: Any, epiteto: Any, determinacion: Any = None) -> str | None:
    """Construye scientificName desde partes. Usa determinacion como fallback."""
    def _limpio(v: Any) -> str | None:
        if pd.isna(v) or str(v).strip() in ("", "nan"):
            return None
        return str(v).strip()

    g = _limpio(genero)
    e = _limpio(epiteto)

    if g and e:
        nombre = f"{g.capitalize()} {e.lower()}"
        return nombre

    det = _limpio(determinacion)
    if det:
        # Limpia anotaciones como "sp." al final
        det = re.sub(r"\s*sp\.\s*$", " sp.", det, flags=re.IGNORECASE).strip()
        return det

    if g:
        return f"{g.capitalize()} sp."

    return None


def normalizar_taxon_rank(genero: Any, epiteto: Any) -> str:
    """Infiere taxonRank desde la presencia de partes del nombre."""
    tiene_genero = pd.notna(genero) and str(genero).strip() not in ("", "nan")
    tiene_epiteto = pd.notna(epiteto) and str(epiteto).strip() not in ("", "nan")
    if tiene_genero and tiene_epiteto:
        return "species"
    if tiene_genero:
        return "genus"
    return "family"


# ── Vocabularios controlados ──────────────────────────────────────────────────

_ESTADO_MAP = {
    "bueno": "present", "regular": "present", "malo": "present",
    "excelente": "present", "deteriorado": "present",
    "extraviado": "absent", "perdido": "absent", "robado": "absent",
    "prestado": "present",
}

_DISPOSICION_MAP = {
    "bueno": "En colección", "excelente": "En colección", "regular": "En colección",
    "malo": "En colección", "deteriorado": "En colección",
    "extraviado": "Extraviado", "perdido": "Extraviado",
    "prestado": "Prestado", "prestamo": "Prestado",
}


def normalizar_occurrence_status(valor: Any) -> str:
    if pd.isna(valor):
        return "present"
    clave = str(valor).lower().strip()
    return _ESTADO_MAP.get(clave, "present")


def normalizar_disposition(valor: Any) -> str | None:
    if pd.isna(valor):
        return None
    clave = str(valor).lower().strip()
    return _DISPOSICION_MAP.get(clave)
