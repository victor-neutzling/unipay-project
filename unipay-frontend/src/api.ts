export type User = {
  id: number;
  name: string;
  email: string;
  cpf: string;
  pixKey: string;
  balance: number;
};

export type Transaction = {
  id: string;
  title: string;
  detail: string;
  date: string;
  amount: number;
  kind: "in" | "out";
  counterpartyCpf?: string | null;
  counterpartyPixKey?: string | null;
};

export type PixRecipient = { name: string; pixKey: string };

type ApiError = { error?: string };
const TOKEN_KEY = "unipay-token";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");

  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`/api${path}`, { ...init, headers });
  const payload = await response.json().catch(() => ({})) as T & ApiError;
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") clearSession();
    throw new Error(payload.error ?? "Não foi possível concluir sua solicitação.");
  }
  return payload;
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
}

export const api = {
  hasSession: () => Boolean(localStorage.getItem(TOKEN_KEY)),
  clearSession,

  async login(email: string, password: string): Promise<User> {
    const result = await request<{ token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem(TOKEN_KEY, result.token);
    return result.user;
  },

  async register(name: string, email: string, cpf: string, password: string): Promise<User> {
    const result = await request<{ user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, cpf, password }),
    });
    return result.user;
  },

  async getAccount(): Promise<User> {
    const result = await request<{ user: User }>("/account");
    return result.user;
  },

  async deposit(amount: number): Promise<{ balance: number }> {
    return request("/account/deposit", { method: "POST", body: JSON.stringify({ amount }) });
  },

  async getTransactions(): Promise<Transaction[]> {
    const result = await request<{ transactions: Transaction[] }>("/account/transactions");
    return result.transactions.map((transaction) => ({
      ...transaction,
      date: new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(transaction.date)),
    }));
  },

  async lookupPixKey(key: string): Promise<PixRecipient> {
    const result = await request<{ recipient: PixRecipient }>(`/pix/lookup?key=${encodeURIComponent(key)}`);
    return result.recipient;
  },

  async getRecentPixRecipients(): Promise<PixRecipient[]> {
    const result = await request<{ recipients: Array<PixRecipient & { criadoEm: string }> }>("/pix/recent");
    return result.recipients.map(({ name, pixKey }) => ({ name, pixKey }));
  },

  async transferPix(pixKey: string, amount: number): Promise<{ receipt: string; balance: number }> {
    return request("/pix/transfers", {
      method: "POST",
      body: JSON.stringify({ pixKey, amount }),
    });
  },
};
