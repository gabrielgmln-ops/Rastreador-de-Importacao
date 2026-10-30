# Rastreador de Processos de Importação

Painel web para acompanhar processos de importação por etapa (PEDIDO → EMBARQUE → CHEGADA → DESEMBARACO → ENTREGA), sinalizar atrasos, medir lead time e puxar o custo estimado da API **Landed**.

Stack: FastAPI + PostgreSQL · React (Vite) + TypeScript · Docker Compose · pytest · GitHub Actions.
**Apenas dados sintéticos.** Fora do escopo: autenticação robusta e integração com o Siscomex.

## Subir

```bash
cp .env.example .env          # troque as senhas e o SECRET_KEY
docker compose --profile simulada up --build -d   # --profile simulada sobe uma Landed fictícia na 8001
docker compose exec api python -m ferramentas.seed  # 6 processos sintéticos
```

- Painel: http://localhost:5173 (usuário/senha: `ADMIN_USER` / `ADMIN_PASSWORD` do `.env`)
- API: http://localhost:8000/docs

Com a Landed real rodando no host na porta 8001, suba sem `--profile simulada`. Contrato em [docs/landed-contrato.md](docs/landed-contrato.md).

## Regras

- **Atraso de etapa:** realizada depois da data prevista, ou pendente com a prevista já vencida.
- **Processo atrasado:** em andamento com alguma etapa atrasada; concluído só se a ENTREGA atrasou.
- **Lead time:** dias entre PEDIDO e ENTREGA reais; o painel mostra a média dos concluídos.
- **Avanço:** registra a data real da etapa atual (não pode ser futura nem anterior à etapa anterior) e passa à próxima.
- **Dinheiro:** `Numeric(14,2)` no banco, `Decimal` no Python, string no JSON. Alterar FOB/frete/seguro invalida o custo calculado.

## API

| Método | Rota | O que faz |
|---|---|---|
| POST | `/auth/login` | devolve token |
| GET/POST | `/processos` | lista (filtros `status`, `etapa`, `atrasado`, `busca`) / cadastra |
| GET/PATCH/DELETE | `/processos/{id}` | detalhe / edita / remove |
| POST | `/processos/{id}/avancar` | conclui a etapa atual |
| PUT | `/processos/{id}/etapas/{tipo}` | replaneja a data prevista |
| POST | `/processos/{id}/custo` | consulta a Landed e grava o custo |
| GET | `/painel` | indicadores |

## Testes

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m pytest          # SQLite em memória; cobertura mínima 90%
```

Para rodar contra PostgreSQL, aponte `TEST_DATABASE_URL` para um banco **dedicado a testes** (os testes recriam as tabelas).

```bash
cd frontend && npm ci && npm test && npm run build
```

O CI (GitHub Actions) roda o back-end contra PostgreSQL 16, o front e o build das imagens.
