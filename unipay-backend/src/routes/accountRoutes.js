import { Router } from "express";
import { pool } from "../db.js";
import { asyncRoute, HttpError } from "../http.js";

export const accountRoutes = Router();

accountRoutes.get("/", asyncRoute(async (request, response) => {
  const [rows] = await pool.execute(
    `SELECT u.idUsuario, u.nome, u.email, u.cpf, u.saldo, cp.chavePix
       FROM usuario AS u
       JOIN chave_pix AS cp ON cp.idUsuario = u.idUsuario
      WHERE u.idUsuario = ?
      LIMIT 1`,
    [request.userId],
  );
  if (!rows[0]) throw new HttpError(404, "Conta não encontrada.");

  const row = rows[0];
  response.json({
    user: {
      id: Number(row.idUsuario),
      name: row.nome,
      email: row.email,
      cpf: row.cpf,
      pixKey: row.chavePix,
      balance: Number(row.saldo),
    },
  });
}));

accountRoutes.post("/deposit", asyncRoute(async (request, response) => {
  const amount = Number(request.body?.amount);
  if (!Number.isFinite(amount) || amount <= 0 || Math.round(amount * 100) / 100 !== amount || !Number.isSafeInteger(Math.round(amount * 100))) {
    throw new HttpError(400, "Informe um valor válido para o depósito.");
  }

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();
    const [accountRows] = await connection.execute(
      "SELECT idUsuario FROM usuario WHERE idUsuario = ? FOR UPDATE",
      [request.userId],
    );
    if (!accountRows[0]) throw new HttpError(404, "Conta não encontrada.");
    const [catalogRows] = await connection.execute(
      `SELECT
         (SELECT idCategoria FROM categoria WHERE tipo = 'Outros' LIMIT 1) AS idCategoria,
         (SELECT idTipoTransacao FROM tipo_transacao WHERE tipo = 'entrada' LIMIT 1) AS idEntrada`,
    );
    const catalog = catalogRows[0];
    if (!catalog?.idCategoria || !catalog?.idEntrada) {
      throw new Error("Os tipos e categorias iniciais do banco não foram carregados.");
    }
    await connection.execute(
      "UPDATE usuario SET saldo = saldo + ? WHERE idUsuario = ?",
      [amount.toFixed(2), request.userId],
    );
    const [counterparty] = await connection.execute(
      "INSERT INTO contraparte (nome, idUsuario, tipo) VALUES ('Depósito UniPay', ?, 'deposito')",
      [request.userId],
    );
    await connection.execute(
      `INSERT INTO transacao (idUsuario, idCategoria, idContraparte, valor, idTipoTransacao)
       VALUES (?, ?, ?, ?, ?)`,
      [request.userId, catalog.idCategoria, counterparty.insertId, amount.toFixed(2), catalog.idEntrada],
    );
    const [balanceRows] = await connection.execute("SELECT saldo FROM usuario WHERE idUsuario = ?", [request.userId]);
    await connection.commit();
    response.status(201).json({ balance: Number(balanceRows[0].saldo) });
  } catch (error) {
    await connection.rollback();
    throw error;
  } finally {
    connection.release();
  }
}));

accountRoutes.get("/transactions", asyncRoute(async (request, response) => {
  const [rows] = await pool.execute(
    `SELECT t.idTransacao, t.valor, t.data, tipo.tipo AS tipoTransacao,
            categoria.tipo AS categoria, contraparte.nome AS contraparte,
            contraparte.cpf AS contraparteCpf,
            contraparteChave.chavePix AS contrapartePixKey,
            contraparte.tipo AS contraparteTipo
       FROM transacao AS t
       JOIN tipo_transacao AS tipo ON tipo.idTipoTransacao = t.idTipoTransacao
       JOIN categoria ON categoria.idCategoria = t.idCategoria
       JOIN contraparte ON contraparte.idContraparte = t.idContraparte
       LEFT JOIN chave_pix AS contraparteChave ON contraparteChave.idUsuario = contraparte.idUsuario
      WHERE t.idUsuario = ?
      ORDER BY t.data DESC, t.idTransacao DESC
      LIMIT 100`,
    [request.userId],
  );

  response.json({
    transactions: rows.map((row) => {
      const incoming = row.tipoTransacao === "entrada";
      const deposit = row.contraparteTipo === "deposito";
      return {
        id: String(row.idTransacao),
        title: deposit ? "Depósito" : incoming ? "PIX recebido" : "PIX enviado",
        detail: deposit ? "Adição de saldo" : `${incoming ? "De" : "Para"} ${row.contraparte}`,
        date: new Date(`${row.data}Z`).toISOString(),
        amount: Number(row.valor),
        kind: incoming ? "in" : "out",
        counterpartyCpf: row.contraparteCpf,
        counterpartyPixKey: row.contrapartePixKey,
      };
    }),
  });
}));
