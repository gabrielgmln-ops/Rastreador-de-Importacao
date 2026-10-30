# rastreador-importacao/backend/app/models.py
# Modelo de dados: um Processo de importação tem exatamente cinco Etapas,
# uma por tipo, cada uma com data prevista e (quando acontecer) data real.
import enum
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TipoEtapa(str, enum.Enum):
    PEDIDO = "PEDIDO"
    EMBARQUE = "EMBARQUE"
    CHEGADA = "CHEGADA"
    DESEMBARACO = "DESEMBARACO"
    ENTREGA = "ENTREGA"


# Ordem oficial do fluxo; usada para avançar e para ordenar as etapas
ORDEM_ETAPAS: list[TipoEtapa] = list(TipoEtapa)

# Dinheiro: Numeric(14, 2) no banco, Decimal no Python. Nunca float.
Dinheiro = Numeric(14, 2)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Processo(Base):
    __tablename__ = "processos"

    id: Mapped[int] = mapped_column(primary_key=True)
    referencia: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    descricao: Mapped[str] = mapped_column(String(200))
    fornecedor: Mapped[str] = mapped_column(String(120))
    pais_origem: Mapped[str] = mapped_column(String(2))  # ISO 3166-1 alfa-2
    ncm: Mapped[str] = mapped_column(String(8))
    moeda: Mapped[str] = mapped_column(String(3), default="USD")
    valor_fob: Mapped[Decimal] = mapped_column(Dinheiro)
    frete: Mapped[Decimal] = mapped_column(Dinheiro, default=Decimal("0"))
    seguro: Mapped[Decimal] = mapped_column(Dinheiro, default=Decimal("0"))

    # Preenchidos pela integração com a Landed (Etapa 4), em BRL
    custo_estimado: Mapped[Decimal | None] = mapped_column(Dinheiro, nullable=True)
    custo_atualizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # native_enum=False grava como texto: portável entre PostgreSQL e SQLite (testes)
    etapa_atual: Mapped[TipoEtapa] = mapped_column(
        Enum(TipoEtapa, native_enum=False, length=20), default=TipoEtapa.PEDIDO
    )
    concluido: Mapped[bool] = mapped_column(default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    etapas: Mapped[list["Etapa"]] = relationship(
        back_populates="processo",
        cascade="all, delete-orphan",
        order_by="Etapa.ordem",
        lazy="selectin",
    )

    def etapa(self, tipo: TipoEtapa) -> "Etapa":
        """Devolve a etapa de um tipo (sempre existe: são criadas juntas)."""
        return next(e for e in self.etapas if e.tipo == tipo)


class Etapa(Base):
    __tablename__ = "etapas"
    __table_args__ = (UniqueConstraint("processo_id", "tipo", name="uq_etapa_processo_tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    processo_id: Mapped[int] = mapped_column(ForeignKey("processos.id", ondelete="CASCADE"))
    tipo: Mapped[TipoEtapa] = mapped_column(Enum(TipoEtapa, native_enum=False, length=20))
    ordem: Mapped[int]
    data_prevista: Mapped[date] = mapped_column(Date)
    data_real: Mapped[date | None] = mapped_column(Date, nullable=True)

    processo: Mapped[Processo] = relationship(back_populates="etapas")
