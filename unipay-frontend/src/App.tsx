import { useEffect, useState, type FormEvent } from "react";
import { api, type PixRecipient, type User } from "./api";
import { FrontPage } from "./pages/FrontPage";
import { LoginPage } from "./pages/LoginPage";
import { PixPage } from "./pages/PixPage";
import { RegisterPage } from "./pages/RegisterPage";
import type { PageName, PixStep } from "./types";

export default function App() {
  const [page, setPage] = useState<PageName>("login");
  const [pixStep, setPixStep] = useState<PixStep>("key");
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [cpf, setCpf] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [recipientKey, setRecipientKey] = useState("");
  const [amount, setAmount] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [recipient, setRecipient] = useState<PixRecipient | null>(null);

  useEffect(() => {
    if (!api.hasSession()) {
      setSessionLoading(false);
      return;
    }

    let active = true;
    api.getAccount()
      .then((account) => {
        if (active) {
          setUser(account);
          setPage("home");
        }
      })
      .catch((sessionError: Error) => {
        if (active) setError(sessionError.message);
      })
      .finally(() => {
        if (active) setSessionLoading(false);
      });

    return () => { active = false; };
  }, []);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const account = await api.login(email, password);
      setUser(account);
      setPassword("");
      setPage("home");
    } catch (loginError) {
      setError((loginError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const account = await api.register(name, email, cpf, password);
      setNotice(`Cadastro realizado! Sua chave PIX é ${account.pixKey}`);
      setPassword("");
      setPage("login");
    } catch (registrationError) {
      setError((registrationError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = () => {
    api.clearSession();
    setUser(null);
    setPage("login");
    setPassword("");
  };

  const handlePixLookup = async () => {
    setBusy(true);
    setError("");
    try {
      const foundRecipient = await api.lookupPixKey(recipientKey);
      setRecipient(foundRecipient);
      setPixStep("amount");
    } catch (lookupError) {
      setError((lookupError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handlePixTransfer = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.transferPix(recipientKey, Number(amount.replace(",", ".")));
      setReceipt(result.receipt);
      setUser((current) => current ? { ...current, balance: result.balance } : current);
      setPixStep("done");
    } catch (transferError) {
      setError((transferError as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (sessionLoading) {
    return <main className="session-loading" role="status">Carregando sua conta…</main>;
  }

  if (page === "register") {
    return (
      <RegisterPage
        onRegister={handleRegister}
        onBack={() => { setError(""); setPage("login"); }}
        name={name} setName={setName}
        email={email} setEmail={setEmail}
        cpf={cpf} setCpf={setCpf}
        password={password} setPassword={setPassword}
        error={error} busy={busy}
      />
    );
  }

  if (page === "home" && user) {
    return <FrontPage user={user} onPix={() => { setError(""); setPixStep("key"); setRecipientKey(""); setRecipient(null); setAmount(""); setPage("pix"); }} onLogout={handleLogout} />;
  }

  if (page === "pix") {
    return (
      <PixPage
        step={pixStep} setStep={setPixStep}
        pixKey={recipientKey} setPixKey={setRecipientKey}
        recipient={recipient} setRecipient={setRecipient}
        amount={amount} setAmount={setAmount}
        error={error} busy={busy} receipt={receipt}
        onLookup={handlePixLookup} onTransfer={handlePixTransfer} onHome={() => setPage("home")}
      />
    );
  }

  return (
    <LoginPage
      onLogin={handleLogin}
      onRegister={() => { setError(""); setNotice(""); setPage("register"); }}
      email={email} setEmail={setEmail}
      password={password} setPassword={setPassword}
      error={error} busy={busy} notice={notice}
    />
  );
}
