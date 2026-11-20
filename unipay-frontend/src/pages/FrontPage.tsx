import { useEffect, useState, type FormEvent } from "react";
import { ArrowLeftRight, ArrowRight } from "lucide-react";
import { api, type Transaction, type User } from "../api";
import { AccountSidebar } from "../components/AccountSidebar";
import { BalanceCard } from "../components/BalanceCard";
import { TransactionDrawer } from "../components/TransactionDrawer";
import { TransactionList } from "../components/TransactionList";

type FrontPageProps = { user: User; onPix: () => void; onLogout: () => void };

export function FrontPage({ user, onPix, onLogout }: FrontPageProps) {
  const now = new Date();
  const dateLabel = new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(now).toLocaleUpperCase("pt-BR");
  const greeting = now.getHours() < 12 ? "Bom dia" : now.getHours() < 18 ? "Boa tarde" : "Boa noite";
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [balanceHidden, setBalanceHidden] = useState(false);
  const [balance, setBalance] = useState(user.balance);
  const [loadError, setLoadError] = useState("");
  const [depositOpen, setDepositOpen] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [depositError, setDepositError] = useState("");
  const [depositBusy, setDepositBusy] = useState(false);

  const handleDeposit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const amount = Number(depositAmount.replace(",", "."));
    if (!Number.isFinite(amount) || amount <= 0 || Math.round(amount * 100) / 100 !== amount || !Number.isSafeInteger(Math.round(amount * 100))) {
      setDepositError("Informe um valor positivo com até duas casas decimais.");
      return;
    }
    setDepositBusy(true);
    setDepositError("");
    try {
      const result = await api.deposit(amount);
      setBalance(result.balance);
      setDepositAmount("");
      setDepositOpen(false);
      try {
        setTransactions(await api.getTransactions());
        setLoadError("");
      } catch (refreshError) {
        setLoadError((refreshError as Error).message);
      }
    } catch (error) {
      setDepositError((error as Error).message);
    } finally {
      setDepositBusy(false);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.all([api.getTransactions(), api.getAccount()])
      .then(([accountTransactions, account]) => {
        if (!active) return;
        setTransactions(accountTransactions);
        setBalance(account.balance);
        setLoadError("");
      })
      .catch((error: Error) => {
        if (active) setLoadError(error.message);
      });
    return () => { active = false; };
  }, []);

  return (
    <main className="dashboard">
      <AccountSidebar onPix={onPix} onLogout={onLogout} />
      <section className="dash-main">
        <div className="dash-header">
          <div><span className="eyebrow">{dateLabel}</span><h1>{greeting}, {user.name.split(" ")[0]} <span className="wave">✳</span></h1><p>Aqui está o resumo da sua conta.</p></div>
          <div className="dash-user"><span className="online-dot" /> Conta pessoal <span className="avatar">{user.name.slice(0, 1).toUpperCase()}</span></div>
        </div>
        {loadError && <p className="error-msg" role="alert">{loadError}</p>}
        <BalanceCard balance={balance} hidden={balanceHidden} onToggle={() => setBalanceHidden(!balanceHidden)} />
        <div className="quick-row">
          <button id="make-pix" className="quick-action pix-action" onClick={onPix}><span className="quick-icon">✳</span><span><strong>Fazer PIX</strong><small>Envie em segundos</small></span><ArrowRight size={17} /></button>
          <button id="open-deposit" className="quick-action" onClick={() => { setDepositOpen(!depositOpen); setDepositError(""); }} aria-expanded={depositOpen}><span className="quick-icon pale">＋</span><span><strong>Adicionar dinheiro</strong><small>Traga dinheiro pra cá</small></span><ArrowRight size={17} /></button>
        </div>
        {depositOpen && <form className="deposit-form" onSubmit={handleDeposit}>
          <label htmlFor="deposit-amount">Valor do depósito</label>
          <div className="deposit-controls"><span>R$</span><input id="deposit-amount" type="number" min="0.01" step="0.01" value={depositAmount} onChange={(event) => setDepositAmount(event.target.value)} placeholder="0,00" required /><button id="confirm-deposit" type="submit" disabled={depositBusy}>{depositBusy ? "Salvando…" : "Confirmar"}</button></div>
          {depositError && <p className="error-msg" role="alert">{depositError}</p>}
        </form>}
        <TransactionList transactions={transactions} user={user} onSelect={setSelectedTransaction} />
        <footer className="dash-footer"><span>UniPay Instituição de Pagamento S.A. · CNPJ 00.000.000/0001-00</span><span>Feito para a vida real <span className="footer-star">✳</span></span></footer>
      </section>
      {selectedTransaction && <TransactionDrawer transaction={selectedTransaction} onClose={() => setSelectedTransaction(null)} />}
    </main>
  );
}
