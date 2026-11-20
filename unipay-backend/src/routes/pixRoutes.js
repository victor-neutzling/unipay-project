import { Router } from "express";
import { pool, withTransaction } from "../db.js";
import { asyncRoute, HttpError, normalizePixKey } from "../http.js";

export const pixRoutes = Router();

pixRoutes.get("/lookup", asyncRoute(async (request, response) => {
  const key = normalizePixKey(request.query.key);
  if (!key || key.length > 60) throw new HttpError(400, "Informe uma chave PIX válida.");

  const [rows] = await pool.execute(
    `SELECT u.nome, cp.chavePix
       FROM chave_pix AS cp
       JOIN usuario AS u ON u.idUsuario = cp.idUsuario
      WHERE cp.chavePix = ?
      LIMIT 1`,
    [key],
  );
  if (!rows[0]) throw new HttpError(404, "Não encontramos uma conta com essa chave PIX.");
  response.json({ recipient: { name: rows[0].nome, pixKey: rows[0].chavePix } });
}));

pixRoutes.get("/recent", asyncRoute(async (request, response) => {
  const [rows] = await pool.execute(
    `SELECT cp.chavePix AS pixKey, u.nome AS name, pr.criadoEm
       FROM pix_recente AS pr
       JOIN chave_pix AS cp ON cp.idChavePix = pr.idChavePix
       JOIN usuario AS u ON u.idUsuario = cp.idUsuario
      WHERE pr.idUsuario = ?
      ORDER BY pr.criadoEm DESC
      LIMIT 10`,
    [request.userId],
  );
  response.json({ recipients: rows });
}));

pixRoutes.post("/transfers", asyncRoute(async (request, response) => {
  const body = request.body ?? {};
  const pixKey = normalizePixKey(body.pixKey);
  const amount = Number(body.amount);
  if (!pixKey || pixKey.length > 60) throw new HttpError(400, "Informe uma chave PIX válida.");
  if (!Number.isFinite(amount) || amount <= 0 || Math.round(amount * 100) / 100 !== amount || !Number.isSafeInteger(Math.round(amount * 100))) {
    throw new HttpError(400, "Informe um valor válido para o PIX.");
  }

  const transfer = await withTransaction(async (connection) => {
    const [recipientRows] = await connection.execute(
      `SELECT u.idUsuario, u.nome, u.cpf, cp.idChavePix, cp.chavePix
         FROM chave_pix AS cp
         JOIN usuario AS u ON u.idUsuario = cp.idUsuario
        WHERE cp.chavePix = ?
        LIMIT 1`,
      [pixKey],
    );
    const recipient = recipientRows[0];
    if (!recipient) throw new HttpError(404, "Não encontramos uma conta com essa chave PIX.");
    if (Number(recipient.idUsuario) === request.userId) {
      throw new HttpError(400, "Escolha uma chave PIX diferente da sua.");
    }

    const [accountRows] = await connection.execute(
      `SELECT idUsuario, nome, cpf, saldo
         FROM usuario
        WHERE idUsuario IN (?, ?)
        ORDER BY idUsuario
        FOR UPDATE`,
      [request.userId, recipient.idUsuario],
    );
    const sender = accountRows.find((account) => Number(account.idUsuario) === request.userId);
    if (!sender) throw new HttpError(404, "Conta de origem não encontrada.");
    if (Number(sender.saldo) < amount) throw new HttpError(409, "Saldo insuficiente para realizar o PIX.");

    const [catalogRows] = await connection.execute(
      `SELECT
         (SELECT idCategoria FROM categoria WHERE tipo = 'PIX' LIMIT 1) AS idCategoria,
         (SELECT idTipoTransacao FROM tipo_transacao WHERE tipo = 'saida' LIMIT 1) AS idSaida,
         (SELECT idTipoTransacao FROM tipo_transacao WHERE tipo = 'entrada' LIMIT 1) AS idEntrada`,
    );
    const catalog = catalogRows[0];
    if (!catalog.idCategoria || !catalog.idSaida || !catalog.idEntrada) {
      throw new Error("Os tipos e categorias iniciais do banco não foram carregados.");
    }

    const [debitResult] = await connection.execute(
      "UPDATE usuario SET saldo = saldo - ? WHERE idUsuario = ? AND saldo >= ?",
      [amount.toFixed(2), request.userId, amount.toFixed(2)],
    );
    if (debitResult.affectedRows !== 1) throw new HttpError(409, "Saldo insuficiente para realizar o PIX.");
    await connection.execute(
      "UPDATE usuario SET saldo = saldo + ? WHERE idUsuario = ?",
      [amount.toFixed(2), recipient.idUsuario],
    );

    const [outgoingCounterparty] = await connection.execute(
      "INSERT INTO contraparte (nome, cpf, idUsuario, tipo) VALUES (?, ?, ?, 'pix')",
      [recipient.nome, recipient.cpf, recipient.idUsuario],
    );
    const [incomingCounterparty] = await connection.execute(
      "INSERT INTO contraparte (nome, cpf, idUsuario, tipo) VALUES (?, ?, ?, 'pix')",
      [sender.nome, sender.cpf, request.userId],
    );

    const [outgoingTransaction] = await connection.execute(
      `INSERT INTO transacao (idUsuario, idCategoria, idContraparte, valor, idTipoTransacao)
       VALUES (?, ?, ?, ?, ?)`,
      [request.userId, catalog.idCategoria, outgoingCounterparty.insertId, amount.toFixed(2), catalog.idSaida],
    );
    await connection.execute(
      `INSERT INTO transacao (idUsuario, idCategoria, idContraparte, valor, idTipoTransacao)
       VALUES (?, ?, ?, ?, ?)`,
      [recipient.idUsuario, catalog.idCategoria, incomingCounterparty.insertId, amount.toFixed(2), catalog.idEntrada],
    );

    await connection.execute(
      `INSERT INTO pix_recente (idUsuario, idChavePix)
       VALUES (?, ?)
       ON DUPLICATE KEY UPDATE criadoEm = CURRENT_TIMESTAMP`,
      [request.userId, recipient.idChavePix],
    );

    const [balanceRows] = await connection.execute(
      "SELECT saldo FROM usuario WHERE idUsuario = ?",
      [request.userId],
    );
    return {
      receipt: `PIX-${outgoingTransaction.insertId}`,
      balance: Number(balanceRows[0].saldo),
      recipient: { name: recipient.nome, pixKey: recipient.chavePix },
    };
  });

  response.status(201).json(transfer);
}));
