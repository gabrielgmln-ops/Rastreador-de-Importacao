# rastreador-importacao/backend/app/rotas.py
# Rotas da API: login, CRUD de processos, avanço de etapa, custo (Landed) e painel.
from datetime import date, datetime, timezone
from enum import Enum

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import regras
from app.auth import credenciais_validas, emitir_token, exige_usuario
from app.db import get_db
from app.landed import LandedIndisponivel, calcular_custo, cliente_landed
from app.models import ORDEM_ETAPAS, Etapa, Processo, TipoEtapa
from app.schemas import (
    AlterarPrevista,
    AvancarEtapa,
    EtapaSaida,
    Login,
    PainelSaida,
    ProcessoAtualizar,
    ProcessoCriar,
    ProcessoSaida,
    Token,
)

publico = APIRouter()
protegido = APIRouter(dependencies=[Depends(exige_usuario)])


class StatusProcesso(str, Enum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDO = "CONCLUIDO"


def hoje() -> date:
    """Isolada numa dependência para os testes poderem fixar a data."""
    return date.today()


def _saida(p: Processo, dia: date) -> ProcessoSaida:
    """Monta a resposta já com os campos calculados (atraso e lead time)."""
    etapas = [
        EtapaSaida(
            tipo=e.tipo,
            ordem=e.ordem,
            data_prevista=e.data_prevista,
            data_real=e.data_real,
            atrasada=regras.etapa_atrasada(e, dia),
            dias_atraso=regras.dias_atraso_etapa(e, dia),
        )
        for e in p.etapas
    ]
    base = ProcessoSaida.model_validate(p, from_attributes=True).model_dump(
        exclude={"etapas", "atrasado", "lead_time_dias"}
    )
    return ProcessoSaida(
        **base,
        etapas=etapas,
        atrasado=regras.processo_atrasado(p, dia),
        lead_time_dias=regras.lead_time_dias(p),
    )


def _buscar(db: Session, processo_id: int) -> Processo:
    p = db.get(Processo, processo_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "processo não encontrado")
    return p


# ---------------------------------------------------------------- login
@publico.post("/auth/login", response_model=Token, tags=["auth"])
def login(dados: Login) -> Token:
    if not credenciais_validas(dados.usuario, dados.senha):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "usuário ou senha inválidos")
    return Token(token=emitir_token(dados.usuario))


# ---------------------------------------------------------------- processos
@protegido.post(
    "/processos", response_model=ProcessoSaida, status_code=201, tags=["processos"]
)
def criar(dados: ProcessoCriar, db: Session = Depends(get_db), dia: date = Depends(hoje)):
    campos = dados.model_dump(exclude={"datas_previstas"})
    p = Processo(**campos, etapa_atual=TipoEtapa.PEDIDO)
    p.etapas = [
        Etapa(tipo=t, ordem=i, data_prevista=dados.datas_previstas[t])
        for i, t in enumerate(ORDEM_ETAPAS, start=1)
    ]
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "referência já cadastrada") from None
    db.refresh(p)
    return _saida(p, dia)


@protegido.get("/processos", response_model=list[ProcessoSaida], tags=["processos"])
def listar(
    status_: StatusProcesso | None = Query(default=None, alias="status"),
    etapa: TipoEtapa | None = None,
    atrasado: bool | None = None,
    busca: str | None = Query(default=None, max_length=60),
    db: Session = Depends(get_db),
    dia: date = Depends(hoje),
):
    consulta = select(Processo).order_by(Processo.criado_em.desc(), Processo.id.desc())
    if status_ is not None:
        consulta = consulta.where(Processo.concluido.is_(status_ == StatusProcesso.CONCLUIDO))
    if etapa is not None:
        consulta = consulta.where(Processo.etapa_atual == etapa)
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(
            Processo.referencia.ilike(termo) | Processo.fornecedor.ilike(termo)
        )
    processos = db.scalars(consulta).all()
    # Atraso depende de "hoje": calculado em Python, não guardado no banco
    if atrasado is not None:
        processos = [p for p in processos if regras.processo_atrasado(p, dia) is atrasado]
    return [_saida(p, dia) for p in processos]


@protegido.get("/processos/{processo_id}", response_model=ProcessoSaida, tags=["processos"])
def detalhar(processo_id: int, db: Session = Depends(get_db), dia: date = Depends(hoje)):
    return _saida(_buscar(db, processo_id), dia)


@protegido.patch("/processos/{processo_id}", response_model=ProcessoSaida, tags=["processos"])
def atualizar(
    processo_id: int,
    dados: ProcessoAtualizar,
    db: Session = Depends(get_db),
    dia: date = Depends(hoje),
):
    p = _buscar(db, processo_id)
    mudancas = dados.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in mudancas.items():
        setattr(p, campo, valor)
    # Mudou valor da mercadoria: o custo antigo deixa de valer
    if mudancas.keys() & {"valor_fob", "frete", "seguro"}:
        p.custo_estimado = None
        p.custo_atualizado_em = None
    db.commit()
    db.refresh(p)
    return _saida(p, dia)


@protegido.delete("/processos/{processo_id}", status_code=204, tags=["processos"])
def remover(processo_id: int, db: Session = Depends(get_db)) -> Response:
    db.delete(_buscar(db, processo_id))
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------- etapas
@protegido.post(
    "/processos/{processo_id}/avancar", response_model=ProcessoSaida, tags=["etapas"]
)
def avancar(
    processo_id: int,
    dados: AvancarEtapa,
    db: Session = Depends(get_db),
    dia: date = Depends(hoje),
):
    """Registra a data real da etapa atual e move o processo para a próxima."""
    p = _buscar(db, processo_id)
    if p.concluido:
        raise HTTPException(status.HTTP_409_CONFLICT, "processo já concluído")
    if dados.data_real > dia:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "data real no futuro")

    indice = ORDEM_ETAPAS.index(p.etapa_atual)
    if indice > 0:
        anterior = p.etapa(ORDEM_ETAPAS[indice - 1]).data_real
        if anterior and dados.data_real < anterior:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"data real anterior à da etapa {ORDEM_ETAPAS[indice - 1].value}",
            )

    p.etapa(p.etapa_atual).data_real = dados.data_real
    if indice == len(ORDEM_ETAPAS) - 1:
        p.concluido = True  # ENTREGA registrada: fim do processo
    else:
        p.etapa_atual = ORDEM_ETAPAS[indice + 1]
    db.commit()
    db.refresh(p)
    return _saida(p, dia)


@protegido.put(
    "/processos/{processo_id}/etapas/{tipo}", response_model=ProcessoSaida, tags=["etapas"]
)
def alterar_prevista(
    processo_id: int,
    tipo: TipoEtapa,
    dados: AlterarPrevista,
    db: Session = Depends(get_db),
    dia: date = Depends(hoje),
):
    """Replaneja a data prevista de uma etapa ainda não realizada."""
    p = _buscar(db, processo_id)
    etapa = p.etapa(tipo)
    if etapa.data_real is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "etapa já realizada")
    etapa.data_prevista = dados.data_prevista
    db.commit()
    db.refresh(p)
    return _saida(p, dia)


# ---------------------------------------------------------------- Landed
@protegido.post("/processos/{processo_id}/custo", response_model=ProcessoSaida, tags=["custo"])
def atualizar_custo(
    processo_id: int,
    db: Session = Depends(get_db),
    cliente: httpx.Client = Depends(cliente_landed),
    dia: date = Depends(hoje),
):
    """Consulta a Landed e grava o custo estimado do processo."""
    p = _buscar(db, processo_id)
    try:
        p.custo_estimado = calcular_custo(p, cliente)
    except LandedIndisponivel as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    p.custo_atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(p)
    return _saida(p, dia)


# ---------------------------------------------------------------- painel
@protegido.get("/painel", response_model=PainelSaida, tags=["painel"])
def painel(db: Session = Depends(get_db), dia: date = Depends(hoje)):
    processos = list(db.scalars(select(Processo)).all())
    return PainelSaida(**regras.calcular_indicadores(processos, dia).__dict__)
