"""
Mapea columnas reales de un DataFrame a términos Darwin Core.

Estrategia en dos capas (según metodología del proyecto):
  1. rapidfuzz — fuzzy matching contra pistas semánticas conocidas
  2. Ollama gemma2:2b — para columnas ambiguas que rapidfuzz no resuelve
"""
import re
import json
import requests
from functools import lru_cache
from rapidfuzz import fuzz, process

from config import COLUMN_HINTS, DWC_FIELDS, OLLAMA_URL, OLLAMA_MODEL, RAPIDFUZZ_THRESHOLD


def _normalizar(col: str) -> str:
    return (col.lower()
            .replace(" ", "_")
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))


@lru_cache(maxsize=256)
def _consultar_ollama(columna: str) -> str | None:
    """Pregunta a Ollama cuál término DwC corresponde a la columna."""
    prompt = (
        f"Eres un experto en Darwin Core (DwC) para colecciones biológicas. "
        f"Dado el nombre de columna '{columna}' de una hoja de cálculo de una colección biológica, "
        f"¿a cuál de estos términos DwC corresponde mejor?: {', '.join(DWC_FIELDS)}. "
        f"Si no corresponde a ninguno responde null. "
        f"Responde SOLO con el nombre exacto del término DwC o null, sin explicación."
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=30,
        )
        r.raise_for_status()
        respuesta = r.json()["message"]["content"].strip().strip('"').strip("'")
        if respuesta.lower() in ("null", "none", "ninguno", ""):
            return None
        if respuesta in DWC_FIELDS:
            return respuesta
        # Busca el término más cercano en la respuesta
        mejor = process.extractOne(respuesta, DWC_FIELDS, scorer=fuzz.ratio)
        if mejor and mejor[1] >= 70:
            return mejor[0]
    except Exception:
        pass
    return None


def mapear_columnas(columnas: list[str]) -> dict[str, str | None]:
    """
    Retorna {columna_original: dwc_term | None} para cada columna.
    Usa rapidfuzz primero; si la confianza es baja, delega a Ollama.
    """
    resultado: dict[str, str | None] = {}
    pendientes: list[str] = []

    for col in columnas:
        norm = _normalizar(col)

        # Capa 0: coincidencia directa con término DwC
        if norm in [f.lower() for f in DWC_FIELDS]:
            match = next(f for f in DWC_FIELDS if f.lower() == norm)
            resultado[col] = match
            continue

        # Capa 1: rapidfuzz contra pistas semánticas
        mejor_hint = process.extractOne(norm, list(COLUMN_HINTS.keys()), scorer=fuzz.partial_ratio)
        if mejor_hint and mejor_hint[1] >= RAPIDFUZZ_THRESHOLD:
            resultado[col] = COLUMN_HINTS[mejor_hint[0]]
            continue

        # También intenta matching directo contra los términos DwC
        mejor_dwc = process.extractOne(norm, [f.lower() for f in DWC_FIELDS], scorer=fuzz.ratio)
        if mejor_dwc and mejor_dwc[1] >= RAPIDFUZZ_THRESHOLD:
            match = next(f for f in DWC_FIELDS if f.lower() == mejor_dwc[0])
            resultado[col] = match
            continue

        pendientes.append(col)

    # Capa 2: Ollama para los ambiguos
    for col in pendientes:
        resultado[col] = _consultar_ollama(col)

    return resultado


def generar_reporte_mapeo(columnas: list[str]) -> dict:
    """Retorna un dict con mapeo, estadísticas y columnas sin mapear."""
    mapeo = mapear_columnas(columnas)
    mapeadas = {k: v for k, v in mapeo.items() if v is not None}
    sin_mapear = [k for k, v in mapeo.items() if v is None]
    dwc_cubiertos = set(mapeadas.values())
    dwc_faltantes = [f for f in DWC_FIELDS if f not in dwc_cubiertos]
    return {
        "mapeo": mapeo,
        "total_columnas": len(columnas),
        "mapeadas": len(mapeadas),
        "sin_mapear": sin_mapear,
        "dwc_cubiertos": list(dwc_cubiertos),
        "dwc_faltantes": dwc_faltantes,
        "cobertura_pct": round(len(dwc_cubiertos) / len(DWC_FIELDS) * 100, 1),
    }
