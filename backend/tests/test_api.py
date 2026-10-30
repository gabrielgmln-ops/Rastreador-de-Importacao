# rastreador-importacao/backend/tests/test_api.py
# API de processos: CRUD, avanço de etapa, filtros e painel. HOJE = 15/06/2026.
from tests.conftest import novo_processo


def criar(c, **kw) -> dict:
    r = c.post("/processos", json=novo_processo(**kw))
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- CRUD
def test_criar_processo_gera_cinco_etapas(autenticado):
    p = criar(autenticado)
    assert p["etapa_atual"] == "PEDIDO"
    assert [e["tipo"] for e in p["etapas"]] == [
        "PEDIDO", "EMBARQUE", "CHEGADA", "DESEMBARACO", "ENTREGA"
    ]
    # Dinheiro volta como string exata, sem float
    assert p["valor_fob"] == "10000.00"
    assert p["seguro"] == "120.50"


def test_referencia_duplicada_409(autenticado):
    criar(autenticado)
    r = autenticado.post("/processos", json=novo_processo())
    assert r.status_code == 409


def test_datas_previstas_fora_de_ordem_422(autenticado):
    datas = novo_processo()["datas_previstas"] | {"EMBARQUE": "2026-05-01"}
    r = autenticado.post("/processos", json=novo_processo(datas_previstas=datas))
    assert r.status_code == 422


def test_faltando_etapa_prevista_422(autenticado):
    datas = novo_processo()["datas_previstas"]
    datas.pop("ENTREGA")
    r = autenticado.post("/processos", json=novo_processo(datas_previstas=datas))
    assert r.status_code == 422


def test_valor_negativo_ou_com_tres_casas_422(autenticado):
    assert autenticado.post("/processos", json=novo_processo(valor_fob="-1")).status_code == 422
    assert autenticado.post("/processos", json=novo_processo(valor_fob="1.001")).status_code == 422


def test_detalhar_e_404(autenticado):
    p = criar(autenticado)
    assert autenticado.get(f"/processos/{p['id']}").json()["referencia"] == "IMP-2026-001"
    assert autenticado.get("/processos/9999").status_code == 404


def test_atualizar_valor_invalida_custo(autenticado, landed):
    p = criar(autenticado)
    autenticado.post(f"/processos/{p['id']}/custo")
    r = autenticado.patch(f"/processos/{p['id']}", json={"valor_fob": "20000.00"})
    assert r.json()["valor_fob"] == "20000.00"
    assert r.json()["custo_estimado"] is None


def test_atualizar_descricao_mantem_custo(autenticado):
    p = criar(autenticado)
    autenticado.post(f"/processos/{p['id']}/custo")
    r = autenticado.patch(f"/processos/{p['id']}", json={"descricao": "Nova descrição"})
    assert r.json()["custo_estimado"] == "98765.43"


def test_remover(autenticado):
    p = criar(autenticado)
    assert autenticado.delete(f"/processos/{p['id']}").status_code == 204
    assert autenticado.get(f"/processos/{p['id']}").status_code == 404


# ---------------------------------------------------------------- etapas
def test_avancar_ate_concluir(autenticado):
    p = criar(
        autenticado,
        datas_previstas={
            "PEDIDO": "2026-05-01", "EMBARQUE": "2026-05-10", "CHEGADA": "2026-05-30",
            "DESEMBARACO": "2026-06-05", "ENTREGA": "2026-06-10",
        },
    )
    datas = ["2026-05-01", "2026-05-10", "2026-05-29", "2026-06-04", "2026-06-09"]
    for d in datas:
        r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": d})
        assert r.status_code == 200, r.text
    final = r.json()
    assert final["concluido"] is True
    assert final["lead_time_dias"] == 39
    assert final["atrasado"] is False
    # Concluído não avança mais
    r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-10"})
    assert r.status_code == 409


def test_avancar_move_etapa_atual(autenticado):
    p = criar(autenticado)
    r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-01"})
    assert r.json()["etapa_atual"] == "EMBARQUE"
    assert r.json()["etapas"][0]["data_real"] == "2026-06-01"


def test_avancar_data_futura_422(autenticado):
    p = criar(autenticado)
    r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-16"})
    assert r.status_code == 422


def test_avancar_data_anterior_a_etapa_anterior_422(autenticado):
    p = criar(autenticado)
    autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-05"})
    r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-04"})
    assert r.status_code == 422


def test_atraso_sinalizado_quando_real_passa_da_prevista(autenticado):
    p = criar(autenticado)
    # PEDIDO previsto 01/06, realizado 03/06: 2 dias de atraso
    r = autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-03"})
    pedido = r.json()["etapas"][0]
    assert pedido["atrasada"] is True and pedido["dias_atraso"] == 2
    assert r.json()["atrasado"] is True


def test_etapa_pendente_vencida_sinaliza_atraso(autenticado):
    # PEDIDO previsto 01/06 ainda pendente em 15/06
    p = criar(autenticado)
    assert p["atrasado"] is True
    assert p["etapas"][0]["dias_atraso"] == 14


def test_replanejar_prevista(autenticado):
    p = criar(autenticado)
    r = autenticado.put(
        f"/processos/{p['id']}/etapas/PEDIDO", json={"data_prevista": "2026-06-20"}
    )
    assert r.json()["etapas"][0]["data_prevista"] == "2026-06-20"
    assert r.json()["atrasado"] is False
    autenticado.post(f"/processos/{p['id']}/avancar", json={"data_real": "2026-06-14"})
    r = autenticado.put(
        f"/processos/{p['id']}/etapas/PEDIDO", json={"data_prevista": "2026-06-25"}
    )
    assert r.status_code == 409


# ---------------------------------------------------------------- filtros e painel
def _cenario(c):
    """Três processos: um atrasado, um em dia e um concluído."""
    atrasado = criar(c, referencia="IMP-A")
    em_dia = criar(
        c,
        referencia="IMP-B",
        fornecedor="Outro Fornecedor SA",
        datas_previstas={
            "PEDIDO": "2026-06-20", "EMBARQUE": "2026-06-30", "CHEGADA": "2026-07-20",
            "DESEMBARACO": "2026-07-25", "ENTREGA": "2026-07-30",
        },
    )
    concl = criar(
        c,
        referencia="IMP-C",
        datas_previstas={
            "PEDIDO": "2026-05-01", "EMBARQUE": "2026-05-05", "CHEGADA": "2026-05-20",
            "DESEMBARACO": "2026-05-25", "ENTREGA": "2026-05-31",
        },
    )
    for d in ["2026-05-01", "2026-05-05", "2026-05-20", "2026-05-25", "2026-05-31"]:
        c.post(f"/processos/{concl['id']}/avancar", json={"data_real": d})
    return atrasado, em_dia, concl


def refs(r) -> set[str]:
    return {p["referencia"] for p in r.json()}


def test_filtros(autenticado):
    _cenario(autenticado)
    c = autenticado
    assert refs(c.get("/processos")) == {"IMP-A", "IMP-B", "IMP-C"}
    assert refs(c.get("/processos", params={"status": "CONCLUIDO"})) == {"IMP-C"}
    assert refs(c.get("/processos", params={"status": "EM_ANDAMENTO"})) == {"IMP-A", "IMP-B"}
    assert refs(c.get("/processos", params={"atrasado": "true"})) == {"IMP-A"}
    assert refs(c.get("/processos", params={"atrasado": "false"})) == {"IMP-B", "IMP-C"}
    assert refs(c.get("/processos", params={"etapa": "PEDIDO"})) == {"IMP-A", "IMP-B"}
    assert refs(c.get("/processos", params={"busca": "outro"})) == {"IMP-B"}
    assert c.get("/processos", params={"status": "XYZ"}).status_code == 422


def test_painel(autenticado):
    _cenario(autenticado)
    ind = autenticado.get("/painel").json()
    assert ind == {
        "total": 3,
        "em_andamento": 2,
        "concluidos": 1,
        "atrasados": 1,
        "lead_time_medio_dias": "30.0",
    }
