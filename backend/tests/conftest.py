# rastreador-importacao/backend/tests/conftest.py
# Infraestrutura dos testes: banco isolado, data fixa, Landed simulada e login pronto.
import os

# Ambiente sintético ANTES de importar a aplicação (Settings lê na importação).
# Atribuição direta (não setdefault): um .env exportado no shell não pode vazar para os testes.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["SECRET_KEY"] = "segredo-de-teste"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "senha-de-teste"
os.environ["LANDED_URL"] = "http://landed.teste"

from datetime import date  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.landed import cliente_landed  # noqa: E402
from app.main import app  # noqa: E402
from app.rotas import hoje  # noqa: E402

# Data fixa: atrasos e lead time ficam determinísticos
HOJE = date(2026, 6, 15)

# TEST_DATABASE_URL aponta para o Postgres no CI; localmente usa SQLite em memória
URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture()
def engine():
    opcoes = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    eng = create_engine(URL, **(opcoes if URL.startswith("sqlite") else {}))
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


class LandedFalsa:
    """Servidor Landed simulado: registra as chamadas e responde o que o teste mandar."""

    def __init__(self) -> None:
        self.chamadas: list[httpx.Request] = []
        self.resposta = httpx.Response(200, json={"custo_total": "98765.43"})

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.chamadas.append(req)
        if isinstance(self.resposta, Exception):
            raise self.resposta
        return self.resposta


@pytest.fixture()
def landed() -> LandedFalsa:
    return LandedFalsa()


@pytest.fixture()
def cliente(engine, landed):
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    def _landed():
        with httpx.Client(
            base_url="http://landed.teste", transport=httpx.MockTransport(landed)
        ) as c:
            yield c

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[hoje] = lambda: HOJE
    app.dependency_overrides[cliente_landed] = _landed
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def autenticado(cliente):
    r = cliente.post("/auth/login", json={"usuario": "admin", "senha": "senha-de-teste"})
    cliente.headers["Authorization"] = f"Bearer {r.json()['token']}"
    return cliente


def novo_processo(**sobrepor) -> dict:
    """Processo sintético válido; cada teste muda só o que precisa."""
    dados = {
        "referencia": "IMP-2026-001",
        "descricao": "Rolamentos industriais (sintético)",
        "fornecedor": "Fornecedor Exemplo Ltd",
        "pais_origem": "CN",
        "ncm": "84821010",
        "moeda": "USD",
        "valor_fob": "10000.00",
        "frete": "1500.00",
        "seguro": "120.50",
        "datas_previstas": {
            "PEDIDO": "2026-06-01",
            "EMBARQUE": "2026-06-10",
            "CHEGADA": "2026-07-05",
            "DESEMBARACO": "2026-07-10",
            "ENTREGA": "2026-07-15",
        },
    }
    dados.update(sobrepor)
    return dados
