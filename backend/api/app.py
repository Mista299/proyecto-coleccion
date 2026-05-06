from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routers import occurrences, taxa, stats, etl

app = FastAPI(
    title="MUA Biodiversidad — API Darwin Core",
    description="Sistema de estandarización de colecciones biológicas bajo Darwin Core. Grupo 6 — Ciencias virtual, UdeA.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(occurrences.router)
app.include_router(taxa.router)
app.include_router(stats.router)
app.include_router(etl.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", tags=["Health"])
def root():
    return {
        "proyecto": "Sistema DwC — Colección de Biología MUA",
        "version": "1.0.0",
        "endpoints": ["/occurrences", "/taxa", "/stats/calidad", "/etl/cargar-directorio"],
        "docs": "/docs",
    }
