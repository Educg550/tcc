export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers:
      options.body !== undefined
        ? { "Content-Type": "application/json", ...(options.headers || {}) }
        : options.headers,
    ...options,
  });
  if (!res.ok) {
    let detail = "Erro na operação";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      /* resposta sem corpo JSON */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function formatPrice(cents: number): string {
  return (cents / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const CATEGORIES = [
  { value: "eletronicos", label: "Eletrônicos" },
  { value: "casa", label: "Casa" },
  { value: "livros", label: "Livros" },
  { value: "moda", label: "Moda" },
  { value: "outros", label: "Outros" },
];

export const CONDITIONS = [
  { value: "novo", label: "Novo" },
  { value: "usado", label: "Usado" },
];

export const ORDER_STATUS: Record<string, string> = {
  pending: "Pendente",
  confirmed: "Confirmado",
  shipped: "Enviado",
  delivered: "Entregue",
  cancelled: "Cancelado",
};
