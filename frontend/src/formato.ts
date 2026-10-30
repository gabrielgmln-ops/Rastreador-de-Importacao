// rastreador-importacao/frontend/src/formato.ts
// Formatação para exibição. Dinheiro: a string Decimal da API só vira número na hora
// de exibir; nenhum cálculo monetário acontece no front.

export function dinheiro(valor: string | null, moeda = "BRL"): string {
  if (valor === null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: moeda }).format(
    Number(valor),
  );
}

export function data(iso: string | null): string {
  if (!iso) return "—";
  // AAAA-MM-DD montado à mão: new Date("2026-06-01") cairia no dia anterior em UTC-3
  const [a, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}

export function hojeIso(): string {
  const h = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${h.getFullYear()}-${p(h.getMonth() + 1)}-${p(h.getDate())}`;
}

/** "1.234,56" (digitado à brasileira) → "1234.56". Continua string: o back-end valida o Decimal. */
export function normalizarDecimal(v: string): string {
  const limpo = v.trim();
  return limpo.includes(",") ? limpo.replace(/\./g, "").replace(",", ".") : limpo;
}
