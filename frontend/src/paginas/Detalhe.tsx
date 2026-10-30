// rastreador-importacao/frontend/src/paginas/Detalhe.tsx
// Detalhe do processo: linha do tempo das etapas, avanço, replanejamento e custo (Landed).
import { useEffect, useState } from "react";
import { api } from "../api";
import type { Tela } from "../App";
import { data, dinheiro, hojeIso } from "../formato";
import { ROTULO_ETAPA, type Processo } from "../tipos";
import { Situacao } from "./Lista";

export default function Detalhe({ id, navegar }: { id: number; navegar: (t: Tela) => void }) {
  const [p, setP] = useState<Processo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [dataReal, setDataReal] = useState(hojeIso());
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    api.detalhar(id).then(setP).catch((e) => setErro(e.message));
  }, [id]);

  // Executa uma ação que devolve o processo atualizado, tratando erro e "ocupado"
  async function acao(f: () => Promise<Processo>) {
    setOcupado(true);
    setErro(null);
    try {
      setP(await f());
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setOcupado(false);
    }
  }

  async function remover() {
    if (!p || !confirm(`Remover o processo ${p.referencia}?`)) return;
    await api.remover(p.id);
    navegar({ nome: "lista" });
  }

  if (!p) return erro ? <p className="erro">{erro}</p> : <p className="sutil">Carregando…</p>;

  return (
    <section>
      <button className="discreto" onClick={() => navegar({ nome: "lista" })}>
        ← Processos
      </button>
      <div className="cabecalho-detalhe">
        <div>
          <h2>
            {p.referencia} <Situacao p={p} />
          </h2>
          <p className="sutil">{p.descricao}</p>
        </div>
        <button className="perigo" onClick={remover}>
          Remover
        </button>
      </div>

      {erro && <p className="erro" role="alert">{erro}</p>}

      <div className="grade-detalhe">
        <div className="cartao">
          <h3>Dados</h3>
          <dl>
            <dt>Fornecedor</dt>
            <dd>{p.fornecedor}</dd>
            <dt>Origem</dt>
            <dd>{p.pais_origem}</dd>
            <dt>NCM</dt>
            <dd>{p.ncm}</dd>
            <dt>Valor FOB</dt>
            <dd>{dinheiro(p.valor_fob, p.moeda)}</dd>
            <dt>Frete</dt>
            <dd>{dinheiro(p.frete, p.moeda)}</dd>
            <dt>Seguro</dt>
            <dd>{dinheiro(p.seguro, p.moeda)}</dd>
            <dt>Lead time</dt>
            <dd>{p.lead_time_dias !== null ? `${p.lead_time_dias} dias` : "em curso"}</dd>
          </dl>
        </div>

        <div className="cartao">
          <h3>Custo estimado (Landed)</h3>
          <p className="numero-grande">{dinheiro(p.custo_estimado)}</p>
          <p className="sutil">
            {p.custo_atualizado_em
              ? `Atualizado em ${new Date(p.custo_atualizado_em).toLocaleString("pt-BR")}`
              : "Ainda não calculado"}
          </p>
          <button disabled={ocupado} onClick={() => acao(() => api.atualizarCusto(p.id))}>
            {ocupado ? "Consultando…" : "Calcular na Landed"}
          </button>
        </div>
      </div>

      <h3>Etapas</h3>
      <ol className="linha-do-tempo">
        {p.etapas.map((e) => {
          const atual = !p.concluido && e.tipo === p.etapa_atual;
          return (
            <li
              key={e.tipo}
              className={[e.data_real ? "feita" : "", atual ? "atual" : "", e.atrasada ? "atrasada" : ""].join(" ")}
            >
              <div className="etapa-nome">{ROTULO_ETAPA[e.tipo]}</div>
              <div className="etapa-datas">
                <span>
                  Prevista:{" "}
                  {e.data_real ? (
                    data(e.data_prevista)
                  ) : (
                    <input
                      type="date"
                      aria-label={`Replanejar ${ROTULO_ETAPA[e.tipo]}`}
                      defaultValue={e.data_prevista}
                      onBlur={(ev) =>
                        ev.target.value &&
                        ev.target.value !== e.data_prevista &&
                        acao(() => api.replanejar(p.id, e.tipo, ev.target.value))
                      }
                    />
                  )}
                </span>
                <span>Real: {data(e.data_real)}</span>
                {e.atrasada && (
                  <span className="selo atraso">
                    {e.dias_atraso} {e.dias_atraso === 1 ? "dia" : "dias"} de atraso
                  </span>
                )}
              </div>
              {atual && (
                <div className="avancar">
                  <input
                    type="date"
                    value={dataReal}
                    max={hojeIso()}
                    onChange={(ev) => setDataReal(ev.target.value)}
                    aria-label="Data real da etapa"
                  />
                  <button
                    className="primario"
                    disabled={ocupado || !dataReal}
                    onClick={() => acao(() => api.avancar(p.id, dataReal))}
                  >
                    Concluir {ROTULO_ETAPA[e.tipo].toLowerCase()}
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
