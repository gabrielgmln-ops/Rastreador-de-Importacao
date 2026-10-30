# rastreador-importacao/backend/tests/test_landed.py
# Integração com a Landed contra um servidor simulado (httpx.MockTransport).
import json

import httpx

from tests.conftest import novo_processo


def test_custo_gravado_e_contrato_enviado(autenticado, landed):
    p = autenticado.post("/processos", json=novo_processo()).json()
    r = autenticado.post(f"/processos/{p['id']}/custo")
    assert r.status_code == 200
    assert r.json()["custo_estimado"] == "98765.43"
    assert r.json()["custo_atualizado_em"] is not None

    # O que foi enviado à Landed: valores como string, sem perda
    req = landed.chamadas[0]
    assert req.url.path == "/calcular"
    assert json.loads(req.content) == {
        "ncm": "84821010",
        "pais_origem": "CN",
        "moeda": "USD",
        "valor_fob": "10000.00",
        "frete": "1500.00",
        "seguro": "120.50",
    }


def test_custo_numerico_vira_decimal_com_duas_casas(autenticado, landed):
    landed.resposta = httpx.Response(200, json={"custo_total": 1234.5})
    p = autenticado.post("/processos", json=novo_processo()).json()
    assert autenticado.post(f"/processos/{p['id']}/custo").json()["custo_estimado"] == "1234.50"


def test_landed_fora_do_ar_502_e_nao_grava(autenticado, landed):
    landed.resposta = httpx.ConnectError("recusada")
    p = autenticado.post("/processos", json=novo_processo()).json()
    r = autenticado.post(f"/processos/{p['id']}/custo")
    assert r.status_code == 502
    assert autenticado.get(f"/processos/{p['id']}").json()["custo_estimado"] is None


def test_landed_erro_http_502(autenticado, landed):
    landed.resposta = httpx.Response(500, json={"erro": "interno"})
    p = autenticado.post("/processos", json=novo_processo()).json()
    assert autenticado.post(f"/processos/{p['id']}/custo").status_code == 502


def test_landed_resposta_invalida_502(autenticado, landed):
    for corpo in ({"outra_coisa": 1}, {"custo_total": "abc"}, {"custo_total": "-5"}):
        landed.resposta = httpx.Response(200, json=corpo)
        p = autenticado.post(
            "/processos", json=novo_processo(referencia=f"IMP-{len(landed.chamadas)}")
        ).json()
        assert autenticado.post(f"/processos/{p['id']}/custo").status_code == 502


def test_custo_processo_inexistente_404(autenticado):
    assert autenticado.post("/processos/999/custo").status_code == 404
