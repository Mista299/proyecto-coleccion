"""Lee archivos Excel/CSV y retorna DataFrames limpios."""
import pandas as pd
from pathlib import Path

_META_KEYWORDS = {"variable", "definicion", "definición", "clase", "unidades",
                  "obligatorio", "campo", "field", "description", "tipo"}


def _es_hoja_metadata(df: pd.DataFrame) -> bool:
    heads = {str(c).lower().strip() for c in df.columns}
    return len(heads & _META_KEYWORDS) >= 2


def cargar_excel(path: Path) -> tuple[pd.DataFrame, str]:
    """Retorna (dataframe, nombre_hoja) de la hoja con datos reales."""
    xf = pd.ExcelFile(path, engine="openpyxl")
    candidatas = []
    for nombre in xf.sheet_names:
        df = xf.parse(nombre)
        if df.empty or _es_hoja_metadata(df):
            continue
        candidatas.append((nombre, df))
    if not candidatas:
        nombre = xf.sheet_names[0]
        return xf.parse(nombre), nombre
    nombre, df = max(candidatas, key=lambda x: len(x[1]))
    return df, nombre


def cargar_archivo(path: Path) -> pd.DataFrame:
    """Acepta .xlsx, .xls, .csv. Retorna DataFrame."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        df, _ = cargar_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path, encoding="utf-8", sep=None, engine="python")
    else:
        raise ValueError(f"Formato no soportado: {suffix}")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def inferir_collection_code(path: Path) -> str:
    name = path.stem.upper()
    if "MAM" in name:
        return "MUA-MAM"
    if "ANF" in name or "AMP" in name:
        return "MUA-ANF"
    if "REP" in name:
        return "MUA-REP"
    if "AVE" in name or "AVI" in name:
        return "MUA-AVE"
    return "MUA-COL"
