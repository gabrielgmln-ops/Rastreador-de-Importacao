# rastreador-importacao/backend/ferramentas/seed.py
# Popula o banco com processos SINTÉTICOS em estágios variados (em dia, atrasado, concluído).
# Uso: docker compose exec api python -m ferramentas.seed
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import ORDEM_ETAPAS, Etapa, Processo

HOJE = date.today()

# (referência, descrição, fornecedor, país, NCM, FOB, início relativo a hoje, etapas feitas, atraso nas reais)
CENARIOS = [
    ("IMP-DEMO-001", "Rolamentos industriais", "Shenzhen Bearings Co (fictícia)", "CN", "84821010", "18500.00", -70, 5, 0),
    ("IMP-DEMO-002", "Painéis solares 550W", "Sol Exemplo GmbH (fictícia)", "DE", "85414300", "42000.00", -40, 3, 4),
    ("IMP-DEMO-003", "Tecido de algodão", "Algodão Demo Ltd (fictícia)", "IN", "52081200", "9800.00", -20, 2, 0),
    ("IMP-DEMO-004", "Componentes eletrônicos", "Chip Exemplo Inc (fictícia)", "US", "85423190", "27350.50", -55, 4, 6),
    ("IMP-DEMO-005", "Máquina de embalagem", "Pack Demo SpA (fictícia)", "IT", "84224090", "63000.00", -5, 1, 0),
    ("IMP-DEMO-006", "Peças automotivas", "Auto Peças Demo (fictícia)", "CN", "87089990", "15200.00", -90, 5, 3),
]

# Dias, a partir do pedido, em que cada etapa está prevista
PRAZOS = [0, 12, 40, 47, 52]


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for ref, desc, forn, pais, ncm, fob, inicio, feitas, atraso in CENARIOS:
            if db.scalar(select(Processo).where(Processo.referencia == ref)):
                continue  # idempotente: rodar duas vezes não duplica
            pedido = HOJE + timedelta(days=inicio)
            p = Processo(
                referencia=ref, descricao=desc, fornecedor=forn, pais_origem=pais, ncm=ncm,
                moeda="USD", valor_fob=Decimal(fob), frete=Decimal("1800.00"), seguro=Decimal("95.00"),
            )
            p.etapas = []
            for i, tipo in enumerate(ORDEM_ETAPAS):
                prevista = pedido + timedelta(days=PRAZOS[i])
                real = None
                if i < feitas:
                    real = min(prevista + timedelta(days=atraso if i > 0 else 0), HOJE)
                p.etapas.append(Etapa(tipo=tipo, ordem=i + 1, data_prevista=prevista, data_real=real))
            p.concluido = feitas == len(ORDEM_ETAPAS)
            p.etapa_atual = ORDEM_ETAPAS[min(feitas, len(ORDEM_ETAPAS) - 1)]
            db.add(p)
        db.commit()
    print(f"seed concluído: {len(CENARIOS)} processos sintéticos")


if __name__ == "__main__":
    main()
