#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera README.md con todo el contenido de los entregables (fases 1 y 2).
Colección de Biología MUA — Grupo 6, Ciencias virtual.
"""
import sys
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

BASE_DIR  = Path(__file__).resolve().parent
MUESTRAS  = BASE_DIR / "muestras"
README    = BASE_DIR / "README.md"

HOY = datetime.today().strftime("%d de %B de %Y")

# ── 16 campos DwC marcados con x en "Colección biológica" (campos.jpeg) ──────
CAMPOS = [
    # (termino, español, entidad, tipo, obligatorio, validacion)
    ("occurrenceID",    "ID del registro biológico", "Occurrence", "string",  "S", "No nulo; formato INST:COLL:ID"),
    ("basisOfRecord",   "Base del registro",         "Occurrence", "string",  "S", "PreservedSpecimen | LivingSpecimen"),
    ("institutionCode", "Código de la institución",  "Occurrence", "string",  "S", "Acrónimo oficial (ej. UDEA)"),
    ("collectionCode",  "Código de la colección",    "Occurrence", "string",  "S", "Ej. MUA-MAM, MUA-ANF"),
    ("catalogNumber",   "Número de catálogo",        "Occurrence", "string",  "S", "Único dentro de la colección"),
    ("occurrenceStatus","Estado del registro",       "Occurrence", "string",  "S", "present | absent"),
    ("disposition",     "Disposición",               "Occurrence", "string",  "N", "En colección | Extraviado | Prestado"),
    ("eventDate",       "Fecha del evento",          "Event",      "string",  "S", "ISO 8601: YYYY-MM-DD"),
    ("country",         "País",                      "Location",   "string",  "S", "Nombre completo del país"),
    ("stateProvince",   "Departamento",              "Location",   "string",  "S", "División administrativa nivel 1"),
    ("county",          "Municipio",                 "Location",   "string",  "N", "División administrativa nivel 2"),
    ("locality",        "Localidad",                 "Location",   "string",  "N", "Descripción del sitio de colecta"),
    ("decimalLatitude", "Latitud decimal",           "Location",   "decimal", "S", "WGS84; rango -90 a 90"),
    ("decimalLongitude","Longitud decimal",          "Location",   "decimal", "S", "WGS84; rango -180 a 180"),
    ("scientificName",  "Nombre científico",         "Taxon",      "string",  "S", "Género Especie Autor Año"),
    ("taxonRank",       "Categoría del taxón",       "Taxon",      "string",  "S", "species | genus | family"),
]

HINTS = {
    "id": "occurrenceID", "catalogo": "catalogNumber", "catalog": "catalogNumber",
    "fecha": "eventDate", "date": "eventDate",
    "pais": "country", "country": "country",
    "depto": "stateProvince", "departamento": "stateProvince", "province": "stateProvince",
    "municipio": "county", "localidad": "locality", "locality": "locality",
    "latitud": "decimalLatitude", "lat": "decimalLatitude",
    "longitud": "decimalLongitude", "lon": "decimalLongitude",
    "nombre": "scientificName", "scientific": "scientificName", "especie": "scientificName",
    "rango": "taxonRank", "rank": "taxonRank", "taxon": "taxonRank",
    "estado": "occurrenceStatus", "disposicion": "disposition",
}

MERMAID = """\
erDiagram
    OCCURRENCE {
        string  occurrenceID    PK
        string  basisOfRecord
        string  institutionCode
        string  collectionCode
        string  catalogNumber
        string  occurrenceStatus
        string  disposition
        string  eventID         FK
        string  taxonID         FK
    }
    EVENT {
        string eventID   PK
        date   eventDate
    }
    LOCATION {
        string  locationID      PK
        string  eventID         FK
        string  country
        string  stateProvince
        string  county
        string  locality
        decimal decimalLatitude
        decimal decimalLongitude
    }
    TAXON {
        string taxonID        PK
        string scientificName
        string taxonRank
    }
    IDENTIFICATION {
        string identificationID PK
        string occurrenceID     FK
        string taxonID          FK
        string identifiedBy
        date   dateIdentified
    }
    OCCURRENCE ||--o| EVENT           : "pertenece a"
    EVENT      ||--|{ LOCATION        : "ocurre en"
    OCCURRENCE ||--o| TAXON           : "clasificado como"
    OCCURRENCE ||--|{ IDENTIFICATION  : "tiene"
    IDENTIFICATION }o--|| TAXON       : "refiere a"
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
# Palabras que indican que una hoja es un diccionario/metadatos, no datos reales
_META_KEYWORDS = {"variable", "definicion", "definición", "clase", "unidades",
                  "obligatorio", "campo", "field", "description", "tipo"}

def leer(path: Path) -> pd.DataFrame:
    """
    Lee la hoja de datos reales del xlsx.
    Estrategia: descarta hojas que parecen diccionarios (sus encabezados contienen
    palabras como 'Variable', 'Definicion', 'Clase', etc.) y elige la hoja con
    más filas entre las restantes.
    """
    xf = pd.ExcelFile(path, engine="openpyxl")
    candidatas = []
    print(f"\n  Hojas en {path.name}:")
    for nombre in xf.sheet_names:
        df = xf.parse(nombre)
        if df.empty:
            print(f"    · '{nombre}' — vacía, ignorada")
            continue
        # Normaliza los encabezados para comparar
        heads = {str(c).lower().strip() for c in df.columns}
        es_meta = len(heads & _META_KEYWORDS) >= 2   # 2+ palabras clave → diccionario
        tag = "[meta/dict]" if es_meta else f"[datos: {len(df):,} filas x {len(df.columns)} cols]"
        print(f"    · '{nombre}' — {tag}")
        if not es_meta:
            candidatas.append((nombre, df))

    if not candidatas:
        # Fallback: la hoja con más filas
        print("  ⚠ Todas las hojas parecen metadatos; usando la de mayor número de filas.")
        dfs = [(n, xf.parse(n)) for n in xf.sheet_names]
        nombre, df = max(dfs, key=lambda x: len(x[1]))
        print(f"  → Usando '{nombre}'")
        return df

    # Elegir la hoja con más filas
    nombre, df = max(candidatas, key=lambda x: len(x[1]))
    print(f"  → Usando '{nombre}'")
    return df


def norm(col: str) -> str:
    return (col.lower()
            .replace(" ","_").replace("á","a").replace("é","e")
            .replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n"))


def presencia_dwc(df: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """Retorna {termino_dwc: (estado, columna_real)} para cada campo del modelo."""
    cols = {norm(c): c for c in df.columns}   # normalizada → nombre original
    resultado = {}
    for term, *_ in CAMPOS:
        tn = term.lower()
        if tn in cols:
            resultado[term] = ("Directa", cols[tn])
        else:
            # busca por palabras clave
            col_real = None
            for hint, dwc in HINTS.items():
                if dwc == term:
                    match = next((cols[nc] for nc in cols if hint in nc), None)
                    if match:
                        col_real = match
                        break
            if col_real:
                resultado[term] = ("Renombre", col_real)
            else:
                resultado[term] = ("Faltante", "—")
    return resultado


def tabla_coincidencias(df_mam: pd.DataFrame, df_anf: pd.DataFrame) -> str:
    """
    Tabla que cruza cada campo del modelo E-R con las columnas reales
    de cada muestra. Muestra el nombre exacto de la columna o '—' si no existe.
    """
    pres_mam = presencia_dwc(df_mam)
    pres_anf = presencia_dwc(df_anf)

    # Encabezados de sección por entidad
    entidad_actual = None
    lines = [
        "| Campo DwC | Entidad | Estado MAM | Columna en MUA_MAM | Estado ANF | Columna en MUA_ANF |\n",
        "|-----------|---------|------------|-------------------|------------|-------------------|\n",
    ]
    for term, _, entidad, *_ in CAMPOS:
        if entidad != entidad_actual:
            entidad_actual = entidad
            lines.append(f"| **— {entidad} —** | | | | | |\n")
        est_m, col_m = pres_mam.get(term, ("Faltante", "—"))
        est_a, col_a = pres_anf.get(term, ("Faltante", "—"))
        col_m_fmt = f"`{col_m}`" if col_m != "—" else "—"
        col_a_fmt = f"`{col_a}`" if col_a != "—" else "—"
        lines.append(
            f"| `{term}` | {entidad} | {est_m} | {col_m_fmt} | {est_a} | {col_a_fmt} |\n"
        )

    # Leyenda
    lines.append("""
**Leyenda**

| Estado | Significado |
|--------|-------------|
| Directa | El nombre de la columna coincide exactamente con el término DwC (insensible a mayúsculas) |
| Renombre | Existe una columna con nombre distinto pero semánticamente equivalente |
| Faltante | El campo no se encontró en el dataset; deberá generarse o completarse en la estandarización |
""")
    return "".join(lines)


def ficha_md(df: pd.DataFrame, nombre: str) -> str:
    total = len(df)
    tipos = df.dtypes.astype(str)
    nulos = df.isnull().sum()
    lines = [f"#### {nombre} — {total:,} registros × {len(df.columns)} columnas\n\n",
             "| # | Columna | Tipo | Nulos | % Nulos | Completitud |\n",
             "|---|---------|------|-------|---------|-------------|\n"]
    for i, col in enumerate(df.columns, 1):
        n  = int(nulos[col])
        pct = round(n / total * 100, 1) if total else 0
        comp = f"{100-pct:.0f}%"
        lines.append(f"| {i} | `{col}` | {tipos[col]} | {n:,} | {pct}% | {comp} |\n")
    lines.append("\n")

    # Head
    lines.append("<details><summary>Primeras 3 filas</summary>\n\n```\n")
    lines.append(df.head(3).to_string())
    lines.append("\n```\n\n</details>\n\n")
    return "".join(lines)


def problemas_md(df: pd.DataFrame, nombre: str) -> tuple[list[dict], str]:
    total = max(len(df), 1)
    prob = []

    for col in df.columns:
        s = df[col]
        n = int(s.isnull().sum())
        if s.dtype == object:
            n += int((s.astype(str).str.strip() == "").sum())
        if n:
            pct = round(n / total * 100, 1)
            prob.append({"tipo": "Campo vacío/nulo", "campo": col, "dataset": nombre,
                         "cantidad": n, "porcentaje": pct,
                         "severidad": "Alta" if pct > 50 else "Media" if pct > 20 else "Baja",
                         "ejemplo": f"'{col}': {n} nulos"})

    id_col = df.columns[0]
    n_dup = int(df.duplicated(subset=[id_col]).sum())
    if n_dup:
        prob.append({"tipo": "Registro duplicado", "campo": id_col, "dataset": nombre,
                     "cantidad": n_dup, "porcentaje": round(n_dup/total*100,1),
                     "severidad": "Alta", "ejemplo": f"Dup en '{id_col}'"})

    for col in df.columns:
        cu = col.upper()
        if any(k in cu for k in ("FECHA","DATE")):
            vals = df[col].dropna().astype(str)
            bad  = int(vals[~vals.str.match(r"^\d{4}-\d{2}-\d{2}$") & (vals.str.strip() != "")].shape[0])
            if bad:
                prob.append({"tipo": "Fecha no ISO 8601", "campo": col, "dataset": nombre,
                             "cantidad": bad, "porcentaje": round(bad/total*100,1),
                             "severidad": "Media", "ejemplo": "No cumple YYYY-MM-DD"})
        if any(k in cu for k in ("LAT","LATITUD")):
            v = pd.to_numeric(df[col], errors="coerce")
            bad = int(((v < -90) | (v > 90)).sum())
            if bad:
                prob.append({"tipo": "Latitud fuera de rango", "campo": col, "dataset": nombre,
                             "cantidad": bad, "porcentaje": round(bad/total*100,1),
                             "severidad": "Alta", "ejemplo": "Fuera de [-90, 90]"})
        if any(k in cu for k in ("LON","LONGITUD")):
            v = pd.to_numeric(df[col], errors="coerce")
            bad = int(((v < -180) | (v > 180)).sum())
            if bad:
                prob.append({"tipo": "Longitud fuera de rango", "campo": col, "dataset": nombre,
                             "cantidad": bad, "porcentaje": round(bad/total*100,1),
                             "severidad": "Alta", "ejemplo": "Fuera de [-180, 180]"})
        if any(k in cu for k in ("NOMBRE","SCIENTIFIC","ESPECIE")):
            vals = df[col].dropna().astype(str)
            bad = int(vals[vals.str.len() > 0][vals[vals.str.len() > 0].str[0].str.islower()].shape[0])
            if bad:
                prob.append({"tipo": "Taxon con minuscula inicial", "campo": col, "dataset": nombre,
                             "cantidad": bad, "porcentaje": round(bad/total*100,1),
                             "severidad": "Baja", "ejemplo": "Nombre no capitalizado"})

    rows = ""
    for p in prob:
        rows += (f"| {p['tipo']} | `{p['campo']}` | {p['dataset']} "
                 f"| {p['cantidad']:,} | {p['porcentaje']}% | {p['severidad']} | {p['ejemplo']} |\n")
    return prob, rows


# ── Construcción del README ───────────────────────────────────────────────────
def construir(df_mam: pd.DataFrame, df_anf: pd.DataFrame) -> str:
    n_mam, n_anf = len(df_mam), len(df_anf)
    df_unif = pd.concat([df_mam.assign(grupo="mamiferos"),
                         df_anf.assign(grupo="anfibios")],
                        ignore_index=True)
    total = len(df_unif)

    prob_mam, rows_mam = problemas_md(df_mam, "MUA_MAM")
    prob_anf, rows_anf = problemas_md(df_anf, "MUA_ANF")
    todos = prob_mam + prob_anf

    completitud_global = round((1 - df_unif.isnull().mean().mean()) * 100, 1)
    total_nulos = int(df_unif.isnull().sum().sum())
    n_dup       = int(df_unif.duplicated().sum())

    # Presencia en cada dataset
    pres_mam = presencia_dwc(df_mam)
    pres_anf = presencia_dwc(df_anf)

    # Top 5 problemas
    if todos:
        df_p = pd.DataFrame(todos)
        top5 = (df_p.groupby("tipo")["cantidad"].sum()
                .sort_values(ascending=False).head(5))
        top5_md = "\n".join(f"{i}. **{t}**: {int(c):,} registros afectados"
                            for i, (t, c) in enumerate(top5.items(), 1))
    else:
        top5_md = "Sin problemas significativos detectados."

    # Tabla campos DwC
    filas_dwc = ""
    for term, esp, entidad, tipo, oblig, valid in CAMPOS:
        pm = pres_mam.get(term, ("Faltante", "—"))[0]
        pa = pres_anf.get(term, ("Faltante", "—"))[0]
        filas_dwc += (f"| `{term}` | {esp} | {entidad} | {tipo} "
                      f"| {'**S**' if oblig=='S' else 'N'} | {valid} | {pm} | {pa} |\n")

    # Tabla resumen de entidades
    from collections import Counter
    conteo_ent = Counter(c[2] for c in CAMPOS)
    resumen_ent = "\n".join(f"| {e} | {n} |" for e, n in conteo_ent.items())

    return f"""\
# Sistema de estandarización de datos bajo el estándar Darwin Core
## Colección de Biología del Museo de la Universidad de Antioquia

**Grupo:** Grupo 6 — Ciencias virtual
**Periodo:** 2026-1
**Fecha de análisis:** {HOY}
**Estándar:** [Darwin Core (TDWG)](https://dwc.tdwg.org/)

---

## Tabla de contenido

1. [Descripción del proyecto](#1-descripción-del-proyecto)
2. [Fase 1 — Análisis y diagnóstico](#2-fase-1--análisis-y-diagnóstico)
   - 2.1 [Revisión de archivos](#21-revisión-de-archivos)
   - 2.2 [Dataset consolidado](#22-dataset-consolidado)
   - 2.3 [Problemas detectados (línea base)](#23-problemas-detectados-línea-base)
3. [Fase 2 — Modelado DwC](#3-fase-2--modelado-dwc)
   - 3.1 [Campos Darwin Core seleccionados](#31-campos-darwin-core-seleccionados)
   - 3.2 [Modelo Entidad-Relación](#32-modelo-entidad-relación)
   - 3.3 [Coincidencia del modelo E-R con los datasets](#33-coincidencia-del-modelo-er-con-los-datasets)
4. [Resumen ejecutivo](#4-resumen-ejecutivo)
5. [Próximos pasos](#5-próximos-pasos)

---

## 1. Descripción del proyecto

El objetivo general es desarrollar un aplicativo que **estandarice y unifique** los datos de la
Colección de Biología del MUA bajo el estándar internacional **Darwin Core (DwC)**.

Este README documenta el trabajo realizado hasta el **21 de abril de 2026**, correspondiente a:

- **Fase 1**: análisis y diagnóstico de los datasets de mamíferos y anfibios.
- **Fase 2 (parcial)**: selección de campos DwC y diseño del modelo entidad-relación.

### Datasets de entrada

| Archivo | Grupo | Registros |
|---------|-------|-----------|
| `muestras/MUA_MAM_20251211.xlsx` | Mamíferos | {n_mam:,} |
| `muestras/MUA-ANF20250131.xlsx`  | Anfibios  | {n_anf:,} |
| **Total consolidado**            |           | **{total:,}** |

### Stack tecnológico

- **Python 3.11+** · pandas · openpyxl · matplotlib · seaborn
- **Estándar:** Darwin Core (TDWG namespace `http://rs.tdwg.org/dwc/terms/`)
- **Futuro:** PostgreSQL · pipeline Python con Ollama + rapidfuzz · interfaz gráfica

---

## 2. Fase 1 — Análisis y diagnóstico

### 2.1 Revisión de archivos

#### 2.1.1 Mamíferos — `MUA_MAM_20251211.xlsx`

{ficha_md(df_mam, "MUA_MAM_20251211.xlsx")}

#### 2.1.2 Anfibios — `MUA-ANF20250131.xlsx`

{ficha_md(df_anf, "MUA-ANF20250131.xlsx")}

---

### 2.2 Dataset consolidado

**Estrategia:** unión vertical (`pd.concat`) porque los dos datasets son grupos taxonómicos
distintos. Se añadió la columna `grupo` (`mamiferos` / `anfibios`) para trazabilidad.

**Dataset unificado:** {total:,} registros × {len(df_unif.columns)} columnas.

#### Columnas del dataset unificado

```
{chr(10).join(f"  {i+1:>2}. {c}" for i, c in enumerate(df_unif.columns))}
```

> Archivo exportado: `fase1/02_dataset_muestra.csv` (UTF-8, separador coma)

---

### 2.3 Problemas detectados (línea base)

Estas métricas son la **referencia** para medir la mejora tras la estandarización DwC.

#### Métricas globales

| Métrica | Valor |
|---------|-------|
| Total de registros | {total:,} |
| Completitud global | {completitud_global}% |
| Celdas nulas/vacías | {total_nulos:,} ({round(total_nulos/(total*len(df_unif.columns))*100,1)}%) |
| Registros duplicados | {n_dup:,} ({round(n_dup/total*100,1)}%) |
| Campos con >50% nulos | {int((df_unif.isnull().mean() > 0.5).sum())} |
| Campos con 20–50% nulos | {int(((df_unif.isnull().mean() >= 0.2) & (df_unif.isnull().mean() <= 0.5)).sum())} |

#### Tabla detallada de problemas

| Problema | Campo | Dataset | Cantidad | % total | Severidad | Ejemplo |
|----------|-------|---------|----------|---------|-----------|---------|
{rows_mam}{rows_anf}
#### Categorías de problemas

| # | Categoría | Descripción |
|---|-----------|-------------|
| 1 | **Fragmentación** | Datos en 2 archivos independientes sin esquema de ID cruzada |
| 2 | **Campos vacíos/nulos** | Ver tabla; localización y taxonomía con mayor vaciedad |
| 3 | **Formato de fechas** | Mezcla de formatos (dd/mm/aaaa, aaaa-mm-dd, solo año) |
| 4 | **Coordenadas** | Algunos registros en grados-minutos-segundos en vez de decimales |
| 5 | **Nombres taxonómicos** | Variaciones de capitalización y abreviaciones de autor |
| 6 | **IDs no estandarizados** | Sin esquema `INST:COLL:ID` en todos los registros |
| 7 | **Versionado manual** | Versión por fecha en el nombre del archivo, sin control formal |

---

## 3. Fase 2 — Modelado DwC

### 3.1 Campos Darwin Core seleccionados

**Fuente:** imagen `campos.jpeg`, columna **"Colección biológica"**
**Total de campos con x:** 16

> **Nota de interpretación:** Se analizó cuidadosamente la columna "Colección biológica" (4ª columna
> de datos) de `campos.jpeg`. Los 16 campos con marca "x" son los listados a continuación.
> La columna "Presencia" indica si el campo ya existe de forma directa, requiere renombre, o está ausente.

#### Tabla completa de campos

| Término DwC | Término en español | Entidad | Tipo | Oblig. | Validación | MUA_MAM | MUA_ANF |
|------------|-------------------|---------|------|--------|-----------|---------|---------|
{filas_dwc}

#### Resumen por entidad DwC

| Entidad | Campos seleccionados |
|---------|---------------------|
{resumen_ent}
| **Identification** *(auxiliar, no en campos.jpeg)* | 5 (en modelo E-R) |
| **Total** | **{len(CAMPOS)}** |

#### Justificación por entidad

**Occurrence (7 campos)**
Identifican unívocamente cada espécimen (`occurrenceID`, `catalogNumber`), establecen la naturaleza
del registro (`basisOfRecord`), vinculan institucionalmente el ejemplar (`institutionCode`,
`collectionCode`) y describen su estado físico actual (`occurrenceStatus`, `disposition`).

**Event (1 campo)**
`eventDate` registra cuándo se realizó la colecta. Fundamental para análisis temporales,
fenológicos y de esfuerzo de muestreo.

**Location (6 campos)**
Jerarquía administrativa (`country`, `stateProvince`, `county`, `locality`) y coordenadas
georreferenciadas (`decimalLatitude`, `decimalLongitude`) indispensables para estudios de distribución.

**Taxon (2 campos)**
`scientificName` y `taxonRank` constituyen la mínima identificación taxonómica estándar requerida
por DwC para cualquier registro biológico.

**Identification (implícita)**
No aparece en `campos.jpeg` pero es una de las 5 entidades canónicas del estándar DwC. Se incluye
en el modelo E-R para registrar determinaciones taxonómicas y el historial de re-identificaciones.

---

### 3.2 Modelo Entidad-Relación

El modelo organiza los 16 campos seleccionados en las **5 entidades canónicas del estándar Darwin Core**,
añadiendo la entidad Identification de forma auxiliar.

#### Relaciones y cardinalidades

| Relación | Cardinalidad | Descripción |
|----------|-------------|-------------|
| OCCURRENCE → EVENT | N:1 | Varios especímenes pueden pertenecer a la misma jornada |
| EVENT → LOCATION | 1:N | Un evento puede asociarse a varias localidades (transecto) |
| OCCURRENCE → TAXON | N:1 | Varios registros pueden tener el mismo nombre científico |
| OCCURRENCE → IDENTIFICATION | 1:N | Un espécimen puede tener múltiples determinaciones |
| IDENTIFICATION → TAXON | N:1 | Cada identificación referencia un taxón |

#### Diagrama E-R

```mermaid
{MERMAID}
```

#### Diccionario de datos

**OCCURRENCE** — 7 campos DwC + 2 FK

| Campo | Tipo SQL | PK/FK | Oblig. | Validación |
|-------|----------|-------|--------|-----------|
| `occurrenceID` | VARCHAR(100) | **PK** | S | No nulo; INST:COLL:ID |
| `basisOfRecord` | VARCHAR(50) | — | S | PreservedSpecimen \| LivingSpecimen |
| `institutionCode` | VARCHAR(20) | — | S | Acrónimo ej. UDEA |
| `collectionCode` | VARCHAR(20) | — | S | Ej. MUA-MAM, MUA-ANF |
| `catalogNumber` | VARCHAR(50) | — | S | Único dentro de la colección |
| `occurrenceStatus` | VARCHAR(20) | — | S | present \| absent |
| `disposition` | VARCHAR(50) | — | N | En colección \| Extraviado \| Prestado |
| `eventID` | VARCHAR(100) | FK→EVENT | N | Referencia EVENT.eventID |
| `taxonID` | VARCHAR(200) | FK→TAXON | N | Referencia TAXON.taxonID |

**EVENT** — 1 campo DwC

| Campo | Tipo SQL | PK/FK | Oblig. | Validación |
|-------|----------|-------|--------|-----------|
| `eventID` | VARCHAR(100) | **PK** | S | Generado por el sistema |
| `eventDate` | DATE | — | S | ISO 8601: YYYY-MM-DD |

**LOCATION** — 6 campos DwC

| Campo | Tipo SQL | PK/FK | Oblig. | Validación |
|-------|----------|-------|--------|-----------|
| `locationID` | VARCHAR(100) | **PK** | S | No nulo |
| `eventID` | VARCHAR(100) | FK→EVENT | S | Referencia EVENT.eventID |
| `country` | VARCHAR(100) | — | S | Nombre completo del país |
| `stateProvince` | VARCHAR(100) | — | S | División adm. nivel 1 |
| `county` | VARCHAR(100) | — | N | División adm. nivel 2 |
| `locality` | TEXT | — | N | Descripción del sitio |
| `decimalLatitude` | DECIMAL(10,7) | — | S | WGS84; rango -90 a 90 |
| `decimalLongitude` | DECIMAL(10,7) | — | S | WGS84; rango -180 a 180 |

**TAXON** — 2 campos DwC

| Campo | Tipo SQL | PK/FK | Oblig. | Validación |
|-------|----------|-------|--------|-----------|
| `taxonID` | VARCHAR(200) | **PK** | S | Clave interna o URI a GBIF/CoL |
| `scientificName` | VARCHAR(300) | — | S | Género Especie Autor Año |
| `taxonRank` | VARCHAR(30) | — | S | species \| genus \| family |

**IDENTIFICATION** — entidad auxiliar (no en campos.jpeg)

| Campo | Tipo SQL | PK/FK | Oblig. | Validación |
|-------|----------|-------|--------|-----------|
| `identificationID` | VARCHAR(100) | **PK** | S | No nulo |
| `occurrenceID` | VARCHAR(100) | FK→OCCURRENCE | S | Referencia OCCURRENCE |
| `taxonID` | VARCHAR(200) | FK→TAXON | N | Referencia TAXON |
| `identifiedBy` | VARCHAR(300) | — | N | Nombre del identificador |
| `dateIdentified` | DATE | — | N | ISO 8601 |

#### Restricciones de integridad

1. `OCCURRENCE.occurrenceID` debe ser globalmente único bajo el esquema `INST:COLL:NNNNNN`.
2. `OCCURRENCE.eventID` puede ser nulo; cuando existe debe referenciar un EVENT válido (integridad referencial).
3. `LOCATION` requiere mínimo `country` y `stateProvince`; las coordenadas son obligatorias cuando existen datos de campo.
4. `TAXON.scientificName` debe seguir el formato `Género specificEpithet [Autor, Año]`.
5. Un OCCURRENCE puede tener múltiples IDENTIFICATION (re-determinaciones); la vigente se marcará con `identificationVerificationStatus = accepted` en fases posteriores.

---

### 3.3 Coincidencia del modelo E-R con los datasets

La siguiente tabla muestra, campo por campo, si existe una columna equivalente en cada muestra
y cuál es su nombre real. Esto permite identificar qué campos requieren transformación y cuáles
deben generarse desde cero durante la estandarización.

{tabla_coincidencias(df_mam, df_anf)}
---

## 4. Resumen ejecutivo

| Métrica | Valor |
|---------|-------|
| Registros mamíferos | {n_mam:,} |
| Registros anfibios | {n_anf:,} |
| **Total consolidado** | **{total:,}** |
| Completitud global | {completitud_global}% |
| Campos DwC seleccionados | {len(CAMPOS)} |
| Entidades DwC modeladas | 5 |

### Top 5 problemas (línea base)

{top5_md}

### Campos seleccionados

{chr(10).join(f"- `{c[0]}` — {c[1]} ({c[2]})" for c in CAMPOS)}

---

## 5. Próximos pasos

Según el cronograma del proyecto (a partir del 22 de abril):

| Etapa | Fechas | Descripción |
|-------|--------|-------------|
| Implementación PostgreSQL | 22 abr – 30 abr | Esquema relacional, tablas de vocabularios, vistas |
| Pipeline Python | 1 – 15 may | ETL con pandas + rapidfuzz + Ollama para normalización taxonómica, fechas y coordenadas |
| Carga masiva | 15 – 22 may | Importación de datos normalizados a PostgreSQL |
| Interfaz gráfica | 22 may – 5 jun | Frontend para consulta y visualización |
| Evaluación | 5 – 15 jun | Comparación de métricas post-estandarización vs. esta línea base |
| Entrega final | 15 – 21 jun | Informe completo, presentación y publicación |

---

*Generado automáticamente el {HOY} · Grupo 6 Ciencias Virtual · Universidad de Antioquia*
"""


def main():
    print("Generando README.md ...")
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("ERROR: pip install openpyxl")
        sys.exit(1)

    p_mam = MUESTRAS / "MUA_MAM_20251211.xlsx"
    p_anf = MUESTRAS / "MUA-ANF20250131.xlsx"
    for p in [p_mam, p_anf]:
        if not p.exists():
            print(f"ERROR: No se encontró {p}")
            sys.exit(1)

    df_mam = leer(p_mam)
    df_anf = leer(p_anf)

    contenido = construir(df_mam, df_anf)
    README.write_text(contenido, encoding="utf-8")
    print(f"✓ README.md generado en {README}")


if __name__ == "__main__":
    main()
