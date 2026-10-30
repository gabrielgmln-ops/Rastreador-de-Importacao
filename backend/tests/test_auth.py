# rastreador-importacao/backend/tests/test_auth.py
# Login simples: credenciais, assinatura e expiração do token.
import time

from app.auth import emitir_token, validar_token


def test_login_ok_devolve_token(cliente):
    r = cliente.post("/auth/login", json={"usuario": "admin", "senha": "senha-de-teste"})
    assert r.status_code == 200
    assert validar_token(r.json()["token"]) == "admin"


def test_login_senha_errada(cliente):
    r = cliente.post("/auth/login", json={"usuario": "admin", "senha": "errada"})
    assert r.status_code == 401


def test_rota_protegida_sem_token(cliente):
    assert cliente.get("/processos").status_code == 401


def test_rota_protegida_com_token_adulterado(cliente):
    token = emitir_token("admin")
    carga, assinatura = token.split(".")
    adulterado = f"{carga}.{assinatura[:-1]}{'A' if assinatura[-1] != 'A' else 'B'}"
    r = cliente.get("/processos", headers={"Authorization": f"Bearer {adulterado}"})
    assert r.status_code == 401


def test_token_expirado():
    antigo = emitir_token("admin", agora=time.time() - 10 * 86400)
    assert validar_token(antigo) is None


def test_token_malformado():
    assert validar_token("lixo") is None
    assert validar_token("a.b.c") is None


def test_health_publico(cliente):
    assert cliente.get("/health").json()["status"] == "ok"
