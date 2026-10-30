# rastreador-importacao/backend/tests/test_regras.py
# Regras puras de atraso, lead time e indicadores, com objetos em memória.
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

from app import regras
from app.models import ORDEM_ETAPAS, Etapa, Processo, TipoEtapa

HOJE = date(2026, 6, 15)


def montar(previstas: Sequence[date], reais: Sequence[date | None], concluido=False) -> Processo:
    p = Processo(referencia="T", concluido=concluido)
    p.etapas = [
        Etapa(tipo=t, ordem=i, data_prevista=prev, data_real=real)
        for i, (t, prev, real) in enumerate(zip(ORDEM_ETAPAS, previstas, reais), start=1)
    ]
    pendentes = [e.tipo for e in p.etapas if e.data_real is None]
    p.etapa_atual = pendentes[0] if pendentes else TipoEtapa.ENTREGA
    return p


PREV = [date(2026, 6, 1) + timedelta(days=10 * i) for i in range(5)]  # 1/6 .. 11/7


def test_etapa_realizada_no_prazo_nao_atrasa():
    e = Etapa(data_prevista=date(2026, 6, 10), data_real=date(2026, 6, 10))
    assert regras.dias_atraso_etapa(e, HOJE) == 0
    assert not regras.etapa_atrasada(e, HOJE)


def test_etapa_realizada_depois_da_prevista_atrasa():
    e = Etapa(data_prevista=date(2026, 6, 10), data_real=date(2026, 6, 13))
    assert regras.dias_atraso_etapa(e, HOJE) == 3


def test_etapa_pendente_vencida_atrasa_contando_ate_hoje():
    e = Etapa(data_prevista=date(2026, 6, 10), data_real=None)
    assert regras.dias_atraso_etapa(e, HOJE) == 5


def test_etapa_pendente_futura_nao_atrasa():
    e = Etapa(data_prevista=date(2026, 6, 20), data_real=None)
    assert not regras.etapa_atrasada(e, HOJE)


def test_processo_com_etapa_atual_vencida_esta_atrasado():
    # PEDIDO ok; EMBARQUE previsto 11/6 ainda pendente em 15/6
    p = montar(PREV, [PREV[0], None, None, None, None])
    assert regras.processo_atrasado(p, HOJE)


def test_processo_com_atraso_passado_continua_atrasado_ate_concluir():
    # EMBARQUE saiu 2 dias depois; a etapa atual ainda está no prazo
    p = montar(PREV, [PREV[0], PREV[1] + timedelta(days=2), None, None, None])
    assert regras.processo_atrasado(p, HOJE)


def test_processo_em_dia():
    p = montar(PREV, [PREV[0], PREV[1], None, None, None])
    assert not regras.processo_atrasado(p, date(2026, 6, 12))


def test_concluido_conta_so_a_entrega():
    reais = [PREV[0], PREV[1] + timedelta(days=3), PREV[2], PREV[3], PREV[4]]
    assert not regras.processo_atrasado(montar(PREV, reais, concluido=True), HOJE)
    reais[-1] = PREV[4] + timedelta(days=1)
    assert regras.processo_atrasado(montar(PREV, reais, concluido=True), HOJE)


def test_lead_time_so_quando_concluido():
    assert regras.lead_time_dias(montar(PREV, [PREV[0], None, None, None, None])) is None
    p = montar(PREV, [date(2026, 6, 1), PREV[1], PREV[2], PREV[3], date(2026, 7, 13)], True)
    assert regras.lead_time_dias(p) == 42


def test_indicadores():
    andamento_atrasado = montar(PREV, [PREV[0], None, None, None, None])
    andamento_em_dia = montar(
        [HOJE + timedelta(days=i) for i in range(5)], [None] * 5
    )
    concluido_a = montar(PREV, [date(2026, 5, 1), *PREV[1:4], date(2026, 6, 10)], True)  # 40 d
    concluido_b = montar(PREV, [date(2026, 5, 1), *PREV[1:4], date(2026, 6, 11)], True)  # 41 d
    ind = regras.calcular_indicadores(
        [andamento_atrasado, andamento_em_dia, concluido_a, concluido_b], HOJE
    )
    assert ind.total == 4
    assert ind.em_andamento == 2
    assert ind.concluidos == 2
    assert ind.atrasados == 1
    assert ind.lead_time_medio_dias == Decimal("40.5")


def test_indicadores_sem_concluidos_nao_tem_lead_time():
    assert regras.calcular_indicadores([], HOJE).lead_time_medio_dias is None
