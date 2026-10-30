// rastreador-importacao/frontend/src/paginas/Login.tsx
import { FormEvent, useState } from "react";
import { api, token } from "../api";

export default function Login({ aoEntrar }: { aoEntrar: () => void }) {
  const [usuario, setUsuario] = useState("admin");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function entrar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const r = await api.login(usuario, senha);
      token.gravar(r.token);
      aoEntrar();
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login">
      <form onSubmit={entrar} className="cartao">
        <h1>Rastreador de Importação</h1>
        <p className="sutil">Acompanhamento de processos por etapa</p>
        <label>
          Usuário
          <input value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="current-password"
            autoFocus
          />
        </label>
        {erro && <p className="erro" role="alert">{erro}</p>}
        <button className="primario" disabled={enviando}>
          {enviando ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
