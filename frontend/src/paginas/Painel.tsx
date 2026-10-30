// rastreador-importacao/frontend/src/paginas/Painel.tsx
// Indicadores: em andamento, atrasados, concluídos e lead time médio.
// Cada cartão leva à lista já filtrada.
import { useEffect, useState } from "react";
import { api } from "../api";
import type { Tela } from "../App";
import type { Painel } from "../tipos";

export default function PainelPagina({ navegar }: { navegar: (t: Tela) => void }) {
  const [dados, setDados] = useState<Painel | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api.painel().then(setDados).catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!dados) return <p className="sutil">Carregando…</p>;

  const lead = dados.lead_time_medio_dias
    ? Number(dados.lead_time_medio_dias).toLocaleString("pt-BR", { maximumFractionDigits: 1 })
    : "—";

  return (
    <section>
      <h2>Painel</h2>
      <div className="indicadores">
        <button
          className="indicador"
          onClick={() => navegar({ nome: "lista", filtros: { status: "EM_ANDAMENTO" } })}
        >
          <span className="numero">{dados.em_andamento}</span>
          <span>Em andamento</span>
        </button>
        <button
          className={`indicador ${dados.atrasados ? "alerta" : ""}`}
          onClick={() => navegar({ nome: "lista", filtros: { atrasado: "true" } })}
        >
          <span className="numero">{dados.atrasados}</span>
          <span>Atrasados</span>
        </button>
        <button
          className="indicador"
          onClick={() => navegar({ nome: "lista", filtros: { status: "CONCLUIDO" } })}
        >
          <span className="numero">{dados.concluidos}</span>
          <span>Concluídos</span>
        </button>
        <div className="indicador">
          <span className="numero">
            {lead}
            {dados.lead_time_medio_dias && <small> dias</small>}
          </span>
          <span>Lead time médio (pedido → entrega)</span>
        </div>
      </div>
      <p className="sutil">{dados.total} processos cadastrados no total.</p>
    </section>
  );
}
