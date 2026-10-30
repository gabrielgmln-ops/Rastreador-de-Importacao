# rastreador-importacao/backend/app/main.py
# Ponto de entrada da API.
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registra as tabelas no metadata)
from app.config import get_settings
from app.db import Base, engine, get_db
from app.rotas import protegido, publico

settings = get_settings()


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    # Projeto pequeno: cria as tabelas na subida. Com o esquema evoluindo, trocar por Alembic.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Rastreador de Processos de Importação",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
def health(db: Session = Depends(get_db)) -> dict:
    """Confirma que a API está de pé e que o banco responde."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok", "env": settings.app_env}


app.include_router(publico)
app.include_router(protegido)
