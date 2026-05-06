#!/usr/bin/env python3
"""
Punto de entrada del backend.

Uso:
  python main.py               → levanta la API en http://localhost:8000
  python main.py --etl         → ejecuta el pipeline ETL sin levantar la API
  python main.py --mapeo       → muestra reporte de mapeo de columnas
"""
import sys
import argparse
from pathlib import Path

# Agrega el venv del proyecto al path si no está activado
_venv = Path(__file__).resolve().parent.parent / ".venv" / "lib"
if _venv.exists():
    import site
    for _p in _venv.glob("python*/site-packages"):
        if str(_p) not in sys.path:
            site.addsitedir(str(_p))


def cmd_api():
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)


def cmd_etl():
    from database import SessionLocal, init_db
    from etl.pipeline import ejecutar_pipeline

    print("Inicializando base de datos...")
    init_db()

    db = SessionLocal()
    try:
        print("Ejecutando pipeline ETL...")
        resultados = ejecutar_pipeline(db)
        for r in resultados:
            print(f"\n── {r.archivo} ──")
            print(f"   Filas procesadas : {r.total_filas}")
            print(f"   Insertados       : {r.insertados}")
            print(f"   Actualizados     : {r.actualizados}")
            print(f"   Omitidos         : {r.omitidos}")
            if r.errores:
                print(f"   Errores ({len(r.errores)}): {r.errores[:3]}")
            print(f"   Mapeo: {r.reporte_mapeo.get('mapeadas', 0)}/{r.reporte_mapeo.get('total_columnas', 0)} columnas mapeadas")
    finally:
        db.close()
    print("\nETL completado.")


def cmd_mapeo():
    from config import MUESTRAS_DIR
    from etl.loader import cargar_archivo
    from etl.mapper import generar_reporte_mapeo

    archivos = list(MUESTRAS_DIR.glob("*.xlsx")) + list(MUESTRAS_DIR.glob("*.csv"))
    for archivo in archivos:
        print(f"\n── {archivo.name} ──")
        df = cargar_archivo(archivo)
        reporte = generar_reporte_mapeo(list(df.columns))
        print(f"   Cobertura DwC: {reporte['cobertura_pct']}%  ({reporte['mapeadas']}/{reporte['total_columnas']} columnas)")
        print(f"   DwC cubiertos : {', '.join(reporte['dwc_cubiertos'])}")
        print(f"   DwC faltantes : {', '.join(reporte['dwc_faltantes'])}")
        if reporte["sin_mapear"]:
            print(f"   Sin mapear    : {reporte['sin_mapear'][:5]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backend MUA Biodiversidad")
    parser.add_argument("--etl", action="store_true", help="Ejecutar pipeline ETL")
    parser.add_argument("--mapeo", action="store_true", help="Mostrar reporte de mapeo")
    args = parser.parse_args()

    if args.etl:
        cmd_etl()
    elif args.mapeo:
        cmd_mapeo()
    else:
        cmd_api()
