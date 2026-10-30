# rastreador-importacao/backend/app/regras.py
# Regras de negócio puras (sem banco, sem HTTP): atraso, lead time e indicadores.
# Ficam isoladas para serem testadas com datas fixas, sem depender de "hoje".
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.models import Etapa, Processo, TipoEtapa


def dias_atraso_etapa(etapa: Etapa, hoje: date) -> int:
    """Dias de atraso de uma etapa.

    - Etapa realizada: atraso = data_real - data_prevista (se positivo).
    - Etapa pendente: já está atrasada se hoje passou da prevista.
    """
    referencia = etapa.data_real or hoje
    return max(0, (referencia - etapa.data_prevista).days)


def etapa_atrasada(etapa: Etapa, hoje: date) -> bool:
    return dias_atraso_etapa(etapa, hoje) > 0


def processo_atrasado(processo: Processo, hoje: date) -> bool:
    """Atrasado se a etapa atual está vencida ou alguma etapa já ocorreu fora do prazo.

    Processo concluído só conta como atrasado se a ENTREGA saiu depois do previsto:
    atrasos intermediários recuperados não mancham um processo entregue no prazo.
    """
    if processo.concluido:
        return etapa_atrasada(processo.etapa(TipoEtapa.ENTREGA), hoje)
    return any(etapa_atrasada(e, hoje) for e in processo.etapas if e.data_real) or etapa_atrasada(
        processo.etapa(processo.etapa_atual), hoje
    )


def lead_time_dias(processo: Processo) -> int | None:
    """Dias entre o PEDIDO e a ENTREGA reais; None enquanto não concluído."""
    pedido = processo.etapa(TipoEtapa.PEDIDO).data_real
    entrega = processo.etapa(TipoEtapa.ENTREGA).data_real
    if not (pedido and entrega):
        return None
    return (entrega - pedido).days


@dataclass(frozen=True)
class Indicadores:
    total: int
    em_andamento: int
    concluidos: int
    atrasados: int
    lead_time_medio_dias: Decimal | None


def calcular_indicadores(processos: list[Processo], hoje: date) -> Indicadores:
    lead_times = [lt for p in processos if (lt := lead_time_dias(p)) is not None]
    medio = None
    if lead_times:
        # Decimal com uma casa: evita 12.333333 no painel e erro de arredondamento binário
        medio = (Decimal(sum(lead_times)) / len(lead_times)).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
    return Indicadores(
        total=len(processos),
        em_andamento=sum(1 for p in processos if not p.concluido),
        concluidos=sum(1 for p in processos if p.concluido),
        atrasados=sum(1 for p in processos if processo_atrasado(p, hoje)),
        lead_time_medio_dias=medio,
    )
