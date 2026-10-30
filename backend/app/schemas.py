# rastreador-importacao/backend/app/schemas.py
# Contratos de entrada e saída da API (Pydantic v2).
# Decimal sai no JSON como string ("1234.56"): o front nunca perde centavos.
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ORDEM_ETAPAS, TipoEtapa


class Login(BaseModel):
    usuario: str
    senha: str


class Token(BaseModel):
    token: str
    tipo: str = "bearer"


class ProcessoCriar(BaseModel):
    referencia: str = Field(min_length=3, max_length=30)
    descricao: str = Field(min_length=3, max_length=200)
    fornecedor: str = Field(min_length=2, max_length=120)
    pais_origem: str = Field(pattern=r"^[A-Z]{2}$")
    ncm: str = Field(pattern=r"^\d{8}$")
    moeda: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    valor_fob: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    frete: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    seguro: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    # Uma data prevista por etapa, as cinco obrigatórias
    datas_previstas: dict[TipoEtapa, date]

    @field_validator("datas_previstas")
    @classmethod
    def valida_previstas(cls, v: dict[TipoEtapa, date]) -> dict[TipoEtapa, date]:
        faltando = [t.value for t in ORDEM_ETAPAS if t not in v]
        if faltando:
            raise ValueError(f"faltam datas previstas para: {', '.join(faltando)}")
        datas = [v[t] for t in ORDEM_ETAPAS]
        if datas != sorted(datas):
            raise ValueError("as datas previstas devem seguir a ordem das etapas")
        return v


class ProcessoAtualizar(BaseModel):
    """Campos editáveis depois do cadastro (todos opcionais)."""

    descricao: str | None = Field(default=None, min_length=3, max_length=200)
    fornecedor: str | None = Field(default=None, min_length=2, max_length=120)
    valor_fob: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    frete: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    seguro: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)


class AvancarEtapa(BaseModel):
    data_real: date


class AlterarPrevista(BaseModel):
    data_prevista: date


class EtapaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: TipoEtapa
    ordem: int
    data_prevista: date
    data_real: date | None
    atrasada: bool = False
    dias_atraso: int = 0


class ProcessoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    referencia: str
    descricao: str
    fornecedor: str
    pais_origem: str
    ncm: str
    moeda: str
    valor_fob: Decimal
    frete: Decimal
    seguro: Decimal
    custo_estimado: Decimal | None
    custo_atualizado_em: datetime | None
    etapa_atual: TipoEtapa
    concluido: bool
    criado_em: datetime
    atrasado: bool = False
    lead_time_dias: int | None = None
    etapas: list[EtapaSaida]


class PainelSaida(BaseModel):
    total: int
    em_andamento: int
    concluidos: int
    atrasados: int
    lead_time_medio_dias: Decimal | None

