// rastreador-importacao/frontend/src/App.tsx
// Casca da aplicação: exige login e alterna entre Painel, Lista, Detalhe e Novo.
// Navegação por estado (sem roteador): são quatro telas, não justifica dependência.
import { useEffect, useState } from "react";
import { definirAoExpirar, token } from "./api";
import Detalhe from "./paginas/Detalhe";
import Lista from "./paginas/Lista";
import Login from "./paginas/Login";
import NovoProcesso from "./paginas/NovoProcesso";
import PainelPagina from "./paginas/Painel";
import type { Filtros } from "./tipos";

export type Tela =
  | { nome: "painel" }
  | { nome: "lista"; filtros?: Filtros }
  | { nome: "detalhe"; id: number }
  | { nome: "novo" };

export default function App() {
  const [logado, setLogado] = useState(() => token.ler() !== null);
  const [tela, setTela] = useState<Tela>({ nome: "painel" });

  useEffect(() => {
    // Token expirado em qualquer chamada: volta ao login
    definirAoExpirar(() => {
      token.gravar(null);
      setLogado(false);
    });
  }, []);

  if (!logado) return <Login aoEntrar={() => setLogado(true)} />;

  const sair = () => {
    token.gravar(null);
    setLogado(false);
  };

  return (
    <div className="casca">
      <header className="topo">
        <strong className="marca">Rastreador de Importação</strong>
        <nav>
          <button
            className={tela.nome === "painel" ? "ativo" : ""}
            onClick={() => setTela({ nome: "painel" })}
          >
            Painel
          </button>
          <button
            className={tela.nome === "lista" || tela.nome === "detalhe" ? "ativo" : ""}
            onClick={() => setTela({ nome: "lista" })}
          >
            Processos
          </button>
          <button className="primario" onClick={() => setTela({ nome: "novo" })}>
            Novo processo
          </button>
          <button className="discreto" onClick={sair}>
            Sair
          </button>
        </nav>
      </header>
      <main className="conteudo">
        {tela.nome === "painel" && <PainelPagina navegar={setTela} />}
        {tela.nome === "lista" && <Lista filtrosIniciais={tela.filtros} navegar={setTela} />}
        {tela.nome === "detalhe" && <Detalhe id={tela.id} navegar={setTela} />}
        {tela.nome === "novo" && <NovoProcesso navegar={setTela} />}
      </main>
    </div>
  );
}
