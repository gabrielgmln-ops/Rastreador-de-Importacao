// rastreador-importacao/frontend/src/api.ts
// Cliente HTTP da API: injeta o token e transforma erros em mensagens legíveis.
import type { Filtros, Painel, Processo, TipoEtapa } from "./tipos";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const CHAVE_TOKEN = "rastreador.token";

export class ErroApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

// sessionStorage: o login some ao fechar a aba (adequado a um login simples)
export const token = {
  ler: (): string | null => {
    try {
      return sessionStorage.getItem(CHAVE_TOKEN);
    } catch {
      return null;
    }
  },
  gravar: (t: string | null) => {
    try {
      if (t) sessionStorage.setItem(CHAVE_TOKEN, t);
      else sessionStorage.removeItem(CHAVE_TOKEN);
    } catch {
      /* armazenamento bloqueado: segue só em memória */
    }
  },
};

let aoExpirar: () => void = () => {};
export const definirAoExpirar = (f: () => void) => (aoExpirar = f);

async function req<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const t = token.ler();
  const resp = await fetch(`${BASE}${caminho}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(t ? { Authorization: `Bearer ${t}` } : {}),
      ...init.headers,
    },
  });
  if (resp.status === 401 && caminho !== "/auth/login") aoExpirar();
  if (!resp.ok) {
    const corpo = await resp.json().catch(() => ({}));
    // FastAPI devolve detail como texto ou como lista de erros de validação
    const detalhe = Array.isArray(corpo.detail)
      ? corpo.detail.map((d: { msg: string }) => d.msg).join("; ")
      : corpo.detail ?? `erro ${resp.status}`;
    throw new ErroApi(resp.status, detalhe);
  }
  return resp.status === 204 ? (undefined as T) : resp.json();
}

const json = (corpo: unknown) => JSON.stringify(corpo);

export const api = {
  login: (usuario: string, senha: string) =>
    req<{ token: string }>("/auth/login", { method: "POST", body: json({ usuario, senha }) }),

  listar: (f: Filtros) => {
    const q = new URLSearchParams(
      Object.entries(f).filter(([, v]) => v !== undefined && v !== "") as [string, string][],
    );
    return req<Processo[]>(`/processos?${q}`);
  },
  detalhar: (id: number) => req<Processo>(`/processos/${id}`),
  criar: (dados: unknown) => req<Processo>("/processos", { method: "POST", body: json(dados) }),
  remover: (id: number) => req<void>(`/processos/${id}`, { method: "DELETE" }),
  avancar: (id: number, data_real: string) =>
    req<Processo>(`/processos/${id}/avancar`, { method: "POST", body: json({ data_real }) }),
  replanejar: (id: number, tipo: TipoEtapa, data_prevista: string) =>
    req<Processo>(`/processos/${id}/etapas/${tipo}`, {
      method: "PUT",
      body: json({ data_prevista }),
    }),
  atualizarCusto: (id: number) => req<Processo>(`/processos/${id}/custo`, { method: "POST" }),
  painel: () => req<Painel>("/painel"),
};
