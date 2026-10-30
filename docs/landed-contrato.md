# Contrato com a API Landed

O Rastreador chama a Landed para obter o **custo estimado** de cada processo, em BRL.

## Requisição

`POST {LANDED_URL}/calcular`

```json
{
  "ncm": "84821010",
  "pais_origem": "CN",
  "moeda": "USD",
  "valor_fob": "10000.00",
  "frete": "1500.00",
  "seguro": "120.50"
}
```

Os valores monetários vão como **string** para não passar por `float`.

## Resposta esperada

```json
{ "custo_total": "98765.43" }
```

Campos extras são ignorados. `custo_total` pode vir como string ou número; o Rastreador converte via `Decimal(str(x))` e arredonda para 2 casas.

## Falhas

| Situação | Comportamento do Rastreador |
|---|---|
| Timeout / conexão recusada | `502`, custo anterior mantido |
| HTTP 4xx/5xx da Landed | `502` |
| Sem `custo_total`, valor não numérico ou negativo | `502` |

Timeout configurável em `LANDED_TIMEOUT_S` (padrão 5 s).

## Desenvolvimento sem a Landed real

`backend/ferramentas/landed_simulada.py` implementa este contrato com câmbio e alíquotas **fictícios**:

```bash
docker compose --profile simulada up --build
```

Se a Landed real usar outro caminho ou outros nomes de campo, o ajuste fica concentrado em `backend/app/landed.py` (`montar_requisicao` e a leitura de `custo_total`).
