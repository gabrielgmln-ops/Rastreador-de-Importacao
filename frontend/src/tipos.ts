// rastreador-importacao/frontend/src/tipos.ts
// Tipos espelhando os contratos da API. Dinheiro chega como string (Decimal) e assim fica.

export const ETAPAS = ["PEDIDO", "EMBARQUE", "CHEGADA", "DESEMBARACO", "ENTREGA"] as const;
export type TipoEtapa = (typeof ETAPAS)[number];

export const ROTULO_ETAPA: Record<TipoEtapa, string> = {
  PEDIDO: "Pedido",
  EMBARQUE: "Embarque",
  CHEGADA: "Chegada",
  DESEMBARACO: "Desembaraço",
  ENTREGA: "Entrega",
};

export interface Etapa {
  tipo: TipoEtapa;
  ordem: number;
  data_prevista: string; // AAAA-MM-DD
  data_real: string | null;
  atrasada: boolean;
  dias_atraso: number;
}

export interface Processo {
  id: number;
  referencia: string;
  descricao: string;
  fornecedor: string;
  pais_origem: string;
  ncm: string;
  moeda: string;
  valor_fob: string;
  frete: string;
  seguro: string;
  custo_estimado: string | null;
  custo_atualizado_em: string | null;
  etapa_atual: TipoEtapa;
  concluido: boolean;
  criado_em: string;
  atrasado: boolean;
  lead_time_dias: number | null;
  etapas: Etapa[];
}

export interface Painel {
  total: number;
  em_andamento: number;
  concluidos: number;
  atrasados: number;
  lead_time_medio_dias: string | null;
}

export interface Filtros {
  status?: "EM_ANDAMENTO" | "CONCLUIDO";
  etapa?: TipoEtapa;
  atrasado?: "true" | "false";
  busca?: string;
}
