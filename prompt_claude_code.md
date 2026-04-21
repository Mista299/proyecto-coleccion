# Prompt para Claude Code — Grupo 6 Ciencias Virtual (hasta 21 abril)

## Contexto del proyecto
Trabajas en el proyecto **"Sistema de estandarización de datos bajo el estándar Darwin Core"** para la Colección de Biología del Museo de la Universidad de Antioquia (Grupo 6 — Ciencias virtual). El objetivo general del proyecto es desarrollar un aplicativo que estandarice y unifique los datos de la colección bajo Darwin Core (DwC).

## Archivos de entrada (ya están en el proyecto local)
- `Grupo 6 ciencias virtual (1).docx` — documento con pregunta de investigación, objetivos, metodología, cronograma y stack tecnológico. **Léelo completo antes de empezar.**
- `campos.jpeg` — imagen que muestra los términos Darwin Core con marcas "x" en varias columnas. **Debes enfocarte únicamente en los campos marcados con "x" en la columna "Colección biológica".** Ignora el resto de columnas para este alcance.
- Carpeta `muestras/` — contiene los únicos datasets disponibles actualmente:
  - `MUA_MAM_20251211.xlsx` (mamíferos)
  - `MUA-ANF20250131.xlsx` (anfibios)
  - No hay más muestras disponibles; trabaja solo con estas dos.

## Alcance: cronograma del .docx hasta el 21 de abril de 2025 inclusive
Debes completar **todas** estas actividades:

### FASE 1 — Análisis y diagnóstico
1. **Revisión de archivos existentes** (9–11 abr): inspecciona los dos .xlsx en `muestras/`, documenta hojas, columnas, tipos, cantidad de registros y formato.
2. **Creación de dataset / muestra representativa** (11–13 abr): consolida ambos datasets en una muestra unificada (considera que son taxones diferentes: mamíferos y anfibios).
3. **Identificación de problemas en la muestra** (13–16 abr): detecta y **cuantifica** problemas de versionado manual, fragmentación de archivos, duplicidad de registros, campos vacíos/nulos e inconsistencias (formatos de fecha, coordenadas, nombres taxonómicos, unidades, mayúsculas/minúsculas, etc.). Las métricas obtenidas serán la **línea base** para la evaluación final del proyecto.

### FASE 2 — Modelado DwC (parcial, hasta 21 abr)
4. **Selección de campos Darwin Core** (17–19 abr): lista exactamente los campos marcados con "x" en la columna **"Colección biológica"** de `campos.jpeg`. Justifica cada uno brevemente. Deben ser entre 20 y 30 campos según el .docx.
5. **Diseño del modelo entidad-relación DwC** (19–21 abr): modelo E-R alineado con el estándar, organizado en las **5 entidades** del estándar DwC (Occurrence, Event, Location, Taxon, Identification), usando **solo** los campos seleccionados en el paso anterior. Define claves primarias, relaciones y validaciones por campo (tipo de dato, obligatoriedad, formato esperado).

**NO hagas** todavía: implementación de PostgreSQL, pipeline Python con Ollama/rapidfuzz, interfaz gráfica, ni carga masiva. Eso es posterior al 21 abr.

## Flujo de trabajo que debes seguir

1. **Primero crea un `TODO.md`** en la raíz del proyecto con una checklist de las 5 actividades anteriores, subdivididas. Actualízalo conforme avances.
2. **Explora antes de escribir código**: lee el .docx, describe lo que ves en `campos.jpeg`, y haz un `df.info()` + `df.head()` + listado de hojas de cada .xlsx.
3. **Mapea las columnas reales de los datasets a los campos DwC** de "Colección biológica": reporta coincidencias directas, renombres necesarios y campos faltantes.
4. **Valida antes de reportar**: comprueba duplicados, nulos por columna, formatos de coordenadas (lat/lon numéricas y en rango), formatos de fecha, y consistencia de `scientificName` / `taxonRank`.
5. **Documenta en Markdown** cada paso antes de generar gráficos o diagramas.

## Entregables y estructura de carpetas

```
entregables/
├── TODO.md
├── RESUMEN.md
├── fase1/
│   ├── 01_revision_archivos.md
│   ├── 02_dataset_muestra.csv
│   ├── 02_proceso_consolidacion.md
│   ├── 03_identificacion_problemas.md
│   └── diagramas/
│       ├── completitud_por_campo.png
│       ├── distribucion_registros.png
│       ├── problemas_detectados.png
│       └── mapa_columnas_a_dwc.png
└── fase2/
    ├── 04_seleccion_campos_dwc.md        # tabla: campo | descripción | obligatorio | tipo | validación
    ├── 05_modelo_entidad_relacion.md     # explicación del modelo + diccionario de datos
    └── diagramas/
        ├── modelo_er.png                  # diagrama E-R completo
        ├── modelo_er.mmd                  # fuente Mermaid del diagrama E-R
        └── entidades_dwc.png              # vista resumen de las 5 entidades DwC
```

## Requisitos de calidad para los diagramas
- **Bonitos y entendibles**, no diagramas genéricos ni feos.
- Usa **Matplotlib/Seaborn** para gráficas de datos (completitud, distribución, problemas) con paleta coherente (sugerencia: tonos tierra/verde museo — `#2E5339`, `#8FB996`, `#C5D86D`, `#F1F0CC`, `#735751`).
- Para el **modelo E-R** usa **Mermaid** (`erDiagram`) y exporta también a PNG. Alternativamente Graphviz si Mermaid no renderiza.
- Títulos en español, leyendas claras, ejes con unidades, sin texto cortado.
- Exporta PNG a **300 dpi** mínimo.
- El diagrama E-R debe mostrar: nombre de entidad, atributos, tipos, PK/FK, cardinalidades y relaciones entre las 5 entidades DwC.

## Requisitos de contenido de los documentos
- `01_revision_archivos.md`: una ficha por dataset con formato, hojas, nº de registros, columnas, tipos, primeras observaciones.
- `03_identificacion_problemas.md`: tabla con **problema | cantidad | % sobre total | severidad | ejemplo**, por cada tipo de problema detectado. Incluye las **métricas línea base** que servirán para el análisis comparativo final.
- `04_seleccion_campos_dwc.md`: tabla completa de los campos de "Colección biológica" con columnas: `término DwC | término en español | entidad DwC | tipo | obligatorio (S/N) | validación | presente en los datasets (S/N/parcial)`.
- `05_modelo_entidad_relacion.md`: descripción de cada entidad, sus atributos, relaciones y cardinalidades. Incluye el código Mermaid dentro del .md además del PNG exportado.
- `RESUMEN.md`: resumen ejecutivo (1 página) con totales de la muestra, top 5 problemas detectados, lista final de campos DwC seleccionados, rutas a los diagramas principales y "próximos pasos" (qué sigue del 21 abr en adelante según el cronograma).

## Restricciones técnicas
- Python 3.11+
- Librerías: `pandas`, `openpyxl`, `matplotlib`, `seaborn`, `pillow`. Para Mermaid→PNG puedes usar `mermaid-cli` (`mmdc`) si está disponible; si no, deja el .mmd y renderiza con Matplotlib o Graphviz.
- No modifiques los archivos originales en `muestras/`: trabaja sobre copias cargadas con pandas.
- Encoding UTF-8 siempre. Todo en español.
- Si encuentras algo ambiguo en `campos.jpeg`, describe tu interpretación en `04_seleccion_campos_dwc.md` antes de avanzar.

## Al terminar
Muéstrame:
1. El árbol de archivos generados en `entregables/`.
2. Un resumen de 5–8 líneas de lo realizado.
3. Cualquier suposición que hayas tenido que hacer.
4. Los "próximos pasos" del cronograma posterior al 21 abr para que yo tenga claro qué sigue.
