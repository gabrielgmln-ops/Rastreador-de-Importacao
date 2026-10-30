# rastreador-importacao/backend/ferramentas/landed_simulada.py
# Landed SIMULADA, só para desenvolvimento local enquanto a Landed real não está no ar.
# Implementa o mesmo contrato (POST /calcular) com alíquotas e câmbio FICTÍCIOS.
# Subir: docker compose --profile simulada up   (porta 8001)
from decimal import ROUND_HALF_UP, Decimal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Landed (simulada)")

CAMBIO = {"USD": Decimal("5.40"), "EUR": Decimal("5.85"), "CNY": Decimal("0.75")}
II, IPI, PIS, COFINS = Decimal("0.14"), Decimal("0.10"), Decimal("0.021"), Decimal("0.0965")
CENTAVO = Decimal("0.01")


class Entrada(BaseModel):
    ncm: str
    pais_origem: str
    moeda: str
    valor_fob: Decimal
    frete: Decimal
    seguro: Decimal


@app.post("/calcular")
def calcular(e: Entrada) -> dict[str, str]:
    cambio = CAMBIO.get(e.moeda, Decimal("5.40"))
    valor_aduaneiro = ((e.valor_fob + e.frete + e.seguro) * cambio).quantize(CENTAVO, ROUND_HALF_UP)
    ii = (valor_aduaneiro * II).quantize(CENTAVO, ROUND_HALF_UP)
    ipi = ((valor_aduaneiro + ii) * IPI).quantize(CENTAVO, ROUND_HALF_UP)
    pis = (valor_aduaneiro * PIS).quantize(CENTAVO, ROUND_HALF_UP)
    cofins = (valor_aduaneiro * COFINS).quantize(CENTAVO, ROUND_HALF_UP)
    total = valor_aduaneiro + ii + ipi + pis + cofins
    return {
        "valor_aduaneiro": str(valor_aduaneiro),
        "tributos": str(ii + ipi + pis + cofins),
        "custo_total": str(total),
        "aviso": "valores simulados",
    }
