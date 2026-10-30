// rastreador-importacao/frontend/src/paginas/NovoProcesso.tsx
// Cadastro de processo com as cinco datas previstas.
import { FormEvent, useState } from "react";
import { api } from "../api";
import { normalizarDecimal as norm } from "../formato";
import type { Tela } from "../App";
import { ETAPAS, ROTULO_ETAPA, type TipoEtapa } from "../tipos";

const VAZIO = {
  referencia: "",
  descricao: "",
  fornecedor: "",
  pais_origem: "CN",
  ncm: "",
  moeda: "USD",
  valor_fob: "",
  frete: "0.00",
  seguro: "0.00",
};

export default function NovoProcesso({ navegar }: { navegar: (t: Tela) => void }) {
  const [campos, setCampos] = useState(VAZIO);
  const [previstas, setPrevistas] = useState<Record<TipoEtapa, string>>(
    Object.fromEntries(ETAPAS.map((t) => [t, ""])) as Record<TipoEtapa, string>,
  );
  const [erro, setErro] = useState<string | null>(null);

  const campo = (nome: keyof typeof VAZIO) => ({
    value: campos[nome],
    onChange: (e: { target: { value: string } }) =>
      setCampos((c) => ({ ...c, [nome]: e.target.value })),
  });

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    try {
      const p = await api.criar({
        ...campos,
        pais_origem: campos.pais_origem.toUpperCase(),
        moeda: campos.moeda.toUpperCase(),
        valor_fob: norm(campos.valor_fob),
        frete: norm(campos.frete),
        seguro: norm(campos.seguro),
        datas_previstas: previstas,
      });
      navegar({ nome: "detalhe", id: p.id });
    } catch (err) {
      setErro((err as Error).message);
    }
  }

  return (
    <section>
      <h2>Novo processo</h2>
      <form className="formulario cartao" onSubmit={salvar}>
        <label>
          Referência
          <input required placeholder="IMP-2026-010" {...campo("referencia")} />
        </label>
        <label className="largo">
          Descrição da mercadoria
          <input required {...campo("descricao")} />
        </label>
        <label>
          Fornecedor
          <input required {...campo("fornecedor")} />
        </label>
        <label>
          País de origem (ISO)
          <input required maxLength={2} {...campo("pais_origem")} />
        </label>
        <label>
          NCM (8 dígitos)
          <input required pattern="\d{8}" inputMode="numeric" {...campo("ncm")} />
        </label>
        <label>
          Moeda
          <input required maxLength={3} {...campo("moeda")} />
        </label>
        <label>
          Valor FOB
          <input required inputMode="decimal" {...campo("valor_fob")} />
        </label>
        <label>
          Frete
          <input inputMode="decimal" {...campo("frete")} />
        </label>
        <label>
          Seguro
          <input inputMode="decimal" {...campo("seguro")} />
        </label>

        <fieldset className="largo">
          <legend>Datas previstas</legend>
          <div className="datas">
            {ETAPAS.map((t) => (
              <label key={t}>
                {ROTULO_ETAPA[t]}
                <input
                  type="date"
                  required
                  value={previstas[t]}
                  onChange={(e) => setPrevistas((p) => ({ ...p, [t]: e.target.value }))}
                />
              </label>
            ))}
          </div>
        </fieldset>

        {erro && <p className="erro largo" role="alert">{erro}</p>}
        <div className="largo acoes">
          <button type="button" className="discreto" onClick={() => navegar({ nome: "lista" })}>
            Cancelar
          </button>
          <button className="primario">Cadastrar</button>
        </div>
      </form>
    </section>
  );
}
