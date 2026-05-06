from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/mua_biodiversidad")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma2:2b")
RAPIDFUZZ_THRESHOLD: int = int(os.getenv("RAPIDFUZZ_THRESHOLD", "80"))
MUESTRAS_DIR: Path = Path(__file__).parent / os.getenv("MUESTRAS_DIR", "../muestras")

INSTITUTION_CODE = "UDEA"

# Campos DwC seleccionados (de campos.jpeg, columna "Colección biológica")
DWC_FIELDS = [
    "occurrenceID", "basisOfRecord", "institutionCode", "collectionCode",
    "catalogNumber", "occurrenceStatus", "disposition",
    "eventDate",
    "country", "stateProvince", "county", "locality",
    "decimalLatitude", "decimalLongitude",
    "scientificName", "taxonRank",
]

# Pistas semánticas para el mapper (hint_keyword → dwc_term)
COLUMN_HINTS: dict[str, str] = {
    "catalogo": "occurrenceID",
    "numero_catalogo": "occurrenceID",
    "catalog": "occurrenceID",
    "fecha": "eventDate",
    "date": "eventDate",
    "pais": "country",
    "country": "country",
    "departamento": "stateProvince",
    "depto": "stateProvince",
    "province": "stateProvince",
    "municipio": "county",
    "localidad": "locality",
    "locality": "locality",
    "latitud": "decimalLatitude",
    "lat": "decimalLatitude",
    "longitud": "decimalLongitude",
    "lon": "decimalLongitude",
    "nombre": "scientificName",
    "scientific": "scientificName",
    "especie": "scientificName",
    "taxon": "taxonRank",
    "rank": "taxonRank",
    "rango": "taxonRank",
    "estado": "occurrenceStatus",
    "disposicion": "disposition",
    "preparacion": "basisOfRecord",
}
