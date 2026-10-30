// rastreador-importacao/frontend/src/paginas/Lista.tsx
// Lista de processos com filtros por status, etapa atual, atraso e busca.
import { useEffect, useState } from "react";
import { api } from "../api";
import type { Tela } from "../App";
import { data, dinheiro } from "../formato";
import { ETAPAS, ROTULO_ETAPA, type Filtros, type Processo, type TipoEtapa } from "../tipos";

interface Props {
  filtrosIniciais?: Filtros;
  navegar: (t: Tela) => void;
}

export default function Lista({ filtrosIniciais = {}, navegar }: Props) {
  const [filtros, setFiltros] = useState<Filtros>(filtrosIniciais);
  const [processos, setProcessos] = useState<Processo[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    // Pequeno atraso na busca textual para não disparar uma requisição por tecla
    const t = setTimeout(() => {
      api.listar(filtros).then(setProcessos).catch((e) => setErro(e.message));
    }, 250);
    return () => clearTimeout(t);
  }, [filtros]);

  const mudar = (campo: keyof Filtros, valor: string) =>
    setFiltros((f) => ({ ...f, [campo]: valor || undefined }));

  return (
    <section>
      <h2>Processos</h2>
      <div className="filtros">
        <input
          placeholder="Buscar referência ou fornecedor"
          value={filtros.busca ?? ""}
          onChange={(e) => mudar("busca", e.target.value)}
        />
        <select value={filtros.status ?? ""} onChange={(e) => mudar("status", e.target.value)}>
          <option value="">Todos os status</option>
          <option value="EM_ANDAMENTO">Em andamento</option>
          <option value="CONCLUIDO">Concluídos</option>
        </select>
        <select value={filtros.etapa ?? ""} onChange={(e) => mudar("etapa", e.target.value)}>
          <option value="">Qualquer etapa</option>
          {ETAPAS.map((t) => (
            <option key={t} value={t}>
              {ROTULO_ETAPA[t]}
            </option>
          ))}
        </select>
        <select value={filtros.atrasado ?? ""} onChange={(e) => mudar("atrasado", e.target.value)}>
          <option value="">Com e sem atraso</option>
          <option value="true">Só atrasados</option>
          <option value="false">Só em dia</option>
        </select>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {!processos && !erro && <p className="sutil">Carregando…</p>}
      {processos?.length === 0 && <p className="sutil">Nenhum processo com esses filtros.</p>}
      {processos && processos.length > 0 && (
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Referência</th>
                <th>Fornecedor</th>
                <th>Etapa</th>
                <th>Próximo prazo</th>
                <th className="num">Custo estimado</th>
                <th>Situação</th>
              </tr>
            </thead>
            <tbody>
              {processos.map((p) => {
                const atual = p.etapas.find((e) => e.tipo === p.etapa_atual)!;
                return (
                  <tr key={p.id} onClick={() => navegar({ nome: "detalhe", id: p.id })}>
                    <td>
                      <strong>{p.referencia}</strong>
                      <div className="sutil">{p.descricao}</div>
                    </td>
                    <td>{p.fornecedor}</td>
                    <td>{p.concluido ? "Entregue" : ROTULO_ETAPA[p.etapa_atual as TipoEtapa]}</td>
                    <td>{p.concluido ? data(atual.data_real) : data(atual.data_prevista)}</td>
                    <td className="num">{dinheiro(p.custo_estimado)}</td>
                    <td>
                      <Situacao p={p} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function Situacao({ p }: { p: Processo }) {
  if (p.atrasado) return <span className="selo atraso">Atrasado</span>;
  if (p.concluido) return <span className="selo ok">Concluído</span>;
  return <span className="selo">Em dia</span>;
}
