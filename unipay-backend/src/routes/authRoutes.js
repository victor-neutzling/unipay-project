import { Router } from "express";
import bcrypt from "bcryptjs";
import { pool, withTransaction } from "../db.js";
import { createToken } from "../auth.js";
import { asyncRoute, HttpError, normalizePixKey, validateCpf } from "../http.js";

export const authRoutes = Router();

function publicUser(row) {
  return {
    id: Number(row.idUsuario),
    name: row.nome,
    email: row.email,
    cpf: row.cpf,
    pixKey: row.chavePix,
    balance: Number(row.saldo),
  };
}

authRoutes.post("/register", asyncRoute(async (request, response) => {
  const body = request.body ?? {};
  const name = String(body.name ?? "").trim();
  const email = normalizePixKey(body.email);
  const cpf = String(body.cpf ?? "").replace(/\D/g, "");
  const password = String(body.password ?? "");

  if (!name || name.length > 255) throw new HttpError(400, "Informe seu nome completo.");
  if (email.length > 255 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new HttpError(400, "Informe um e-mail válido.");
  }
  if (!validateCpf(cpf)) throw new HttpError(400, "Informe um CPF válido.");
  if (password.length < 8 || bcrypt.truncates(password)) {
    throw new HttpError(400, "A senha deve ter pelo menos 8 caracteres e no máximo 72 bytes em UTF-8.");
  }

  const passwordHash = await bcrypt.hash(password, 12);
  const user = await withTransaction(async (connection) => {
    const [insertResult] = await connection.execute(
      "INSERT INTO usuario (nome, email, cpf, senha, saldo) VALUES (?, ?, ?, ?, 0.00)",
      [name, email, cpf, passwordHash],
    );
    const userId = insertResult.insertId;
    await connection.execute(
      "INSERT INTO chave_pix (idUsuario, chavePix) VALUES (?, ?)",
      [userId, email],
    );
    return { id: userId, name, email, cpf, pixKey: email, balance: 0 };
  });

  response.status(201).json({ user });
}));

authRoutes.post("/login", asyncRoute(async (request, response) => {
  const body = request.body ?? {};
  const email = normalizePixKey(body.email);
  const password = String(body.password ?? "");
  if (!email || !password) throw new HttpError(400, "Informe seu e-mail e sua senha.");

  const [rows] = await pool.execute(
    `SELECT u.idUsuario, u.nome, u.email, u.cpf, u.senha, u.saldo, cp.chavePix
       FROM usuario AS u
       JOIN chave_pix AS cp ON cp.idUsuario = u.idUsuario
      WHERE u.email = ?
      LIMIT 1`,
    [email],
  );
  const account = rows[0];
  const passwordMatches = account && await bcrypt.compare(password, account.senha);
  if (!passwordMatches) throw new HttpError(401, "E-mail ou senha incorretos.");

  response.json({ token: createToken(account.idUsuario), user: publicUser(account) });
}));
