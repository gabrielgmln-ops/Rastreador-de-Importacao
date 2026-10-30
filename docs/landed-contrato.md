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
| HTTP 5xx (ou 4xx que não seja 422) da Landed | `502` |
| Sem `custo_total`, valor não numérico ou negativo | `502` |

Timeout configurável em `LANDED_TIMEOUT_S` (padrão 5 s).

## Onde roda

A Landed é um projeto próprio: https://github.com/gabrielgmln-ops/Landed. Ela aceita também `uf` (padrão SP) e `modal` (padrão MARITIMO); o Rastreador usa os padrões.

| Situação | Comportamento do Rastreador |
|---|---|
| Landed responde `422` (ex.: NCM fora da tabela) | `422` com o motivo da Landed |

Para subir: `docker compose up -d` no repositório da Landed (porta 8001). O Rastreador a encontra por `LANDED_URL=http://host.docker.internal:8001`.
