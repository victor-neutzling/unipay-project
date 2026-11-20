import { ArrowDownLeft, ArrowUpRight, X } from "lucide-react";
import type { Transaction } from "../api";

const formatMoney = (value: number) => value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const formatCpf = (cpf?: string | null) => cpf?.replace(/\D/g, "").replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4") ?? "";

type TransactionDrawerProps = { transaction: Transaction; onClose: () => void };

export function TransactionDrawer({ transaction, onClose }: TransactionDrawerProps) {
  const incoming = transaction.kind === "in";
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="transaction-drawer" onClick={(event) => event.stopPropagation()} aria-label="Detalhes da movimentação">
        <div className="drawer-head"><span className="eyebrow">DETALHES DA MOVIMENTAÇÃO</span><button id="close-drawer" onClick={onClose} aria-label="Fechar detalhes"><X size={20} /></button></div>
        <div className={`drawer-icon ${transaction.kind}`}>{incoming ? <ArrowDownLeft size={22} /> : <ArrowUpRight size={22} />}</div>
        <h2>{transaction.title}</h2>
        <p>{transaction.detail}</p>
        <strong id="receipt-amount" className={`drawer-amount ${transaction.kind}`}>{incoming ? "+" : "−"} {formatMoney(transaction.amount)}</strong>
        <div className="drawer-info">
          <span>Data e horário<strong id="receipt-date">{transaction.date}</strong></span>
          {transaction.title.startsWith("PIX") && <>
            <span>{incoming ? "Remetente" : "Destinatário"}<strong id="receipt-recipient">{transaction.detail.replace(/^(De|Para)\s+/, "")}</strong></span>
            <span>{incoming ? "CPF do remetente" : "CPF do destinatário"}<strong id="receipt-cpf">{formatCpf(transaction.counterpartyCpf) || "Não informado"}</strong></span>
            <span>{incoming ? "Chave PIX / e-mail do remetente" : "Chave PIX / e-mail do destinatário"}<strong id="receipt-pix-key">{transaction.counterpartyPixKey || "Não informado"}</strong></span>
          </>}
          <span>Tipo de movimentação<strong>{incoming ? "Entrada" : "Saída"}</strong></span>
          <span>Identificador<strong>{transaction.id.toUpperCase()}</strong></span>
          <span>Status<strong id="receipt-status" className="receipt-status">Concluída</strong></span>
        </div>
        <button id="drawer-ok" className="drawer-done" onClick={onClose}>Tudo certo</button>
      </aside>
    </div>
  );
}
