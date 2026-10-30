# rastreador-importacao/backend/app/landed.py
# Cliente da API Landed (cálculo de custo de importação).
#
# Contrato esperado (documentado em docs/landed-contrato.md):
#   POST {LANDED_URL}/calcular
#   corpo:    {"ncm", "pais_origem", "moeda", "valor_fob", "frete", "seguro"}  (valores como string)
#   resposta: {"custo_total": "12345.67", ...}  em BRL
import logging
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation

import httpx

from app.config import get_settings
from app.models import Processo

log = logging.getLogger(__name__)


class LandedIndisponivel(Exception):
    """A Landed não respondeu, respondeu erro ou devolveu algo inválido."""


class LandedRecusou(Exception):
    """A Landed respondeu, mas recusou os dados do processo (HTTP 422)."""


def _detalhe(resp: httpx.Response) -> str:
    try:
        detalhe = resp.json().get("detail")
    except ValueError:
        detalhe = None
    # FastAPI manda texto ou lista de erros de validação
    if isinstance(detalhe, list):
        detalhe = "; ".join(str(d.get("msg", d)) for d in detalhe)
    return f"a Landed recusou o cálculo: {detalhe or 'dados inválidos'}"


def cliente_landed() -> Iterator[httpx.Client]:
    """Dependência do FastAPI: um cliente HTTP por requisição, sempre fechado.
    Nos testes é substituída por um cliente com transporte simulado."""
    s = get_settings()
    with httpx.Client(base_url=s.landed_url, timeout=s.landed_timeout_s) as cliente:
        yield cliente


def montar_requisicao(processo: Processo) -> dict[str, str]:
    # Decimal vira string para atravessar o JSON sem virar float
    return {
        "ncm": processo.ncm,
        "pais_origem": processo.pais_origem,
        "moeda": processo.moeda,
        "valor_fob": str(processo.valor_fob),
        "frete": str(processo.frete),
        "seguro": str(processo.seguro),
    }


def calcular_custo(processo: Processo, cliente: httpx.Client) -> Decimal:
    """Pede à Landed o custo estimado do processo, em BRL, com duas casas."""
    try:
        resp = cliente.post("/calcular", json=montar_requisicao(processo))
        if resp.status_code == 422:
            # A Landed recusou a entrada (ex.: NCM fora da tabela): repassa o motivo dela
            raise LandedRecusou(_detalhe(resp))
        resp.raise_for_status()
        bruto = resp.json()["custo_total"]
        # str() antes do Decimal: se a Landed mandar número, não herdamos erro de float
        custo = Decimal(str(bruto)).quantize(Decimal("0.01"))
    except httpx.HTTPError as exc:
        log.warning("Landed indisponível: %s", exc)
        raise LandedIndisponivel(f"falha ao chamar a Landed: {exc.__class__.__name__}") from exc
    except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
        raise LandedIndisponivel("resposta da Landed em formato inesperado") from exc
    if custo < 0:
        raise LandedIndisponivel("a Landed devolveu custo negativo")
    return custo
