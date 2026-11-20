import "dotenv/config";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import { ensureCounterpartySchema, pool } from "./db.js";
import { requireAuth } from "./auth.js";
import { HttpError } from "./http.js";
import { accountRoutes } from "./routes/accountRoutes.js";
import { authRoutes } from "./routes/authRoutes.js";
import { pixRoutes } from "./routes/pixRoutes.js";

const app = express();
const port = Number(process.env.API_PORT ?? 3001);
const allowedOrigins = (process.env.CORS_ORIGINS ?? "http://localhost:5173,http://localhost:8080")
  .split(",")
  .map((origin) => origin.trim());

app.disable("x-powered-by");
app.use(helmet());
app.use(cors({ origin: allowedOrigins }));
app.use(express.json({ limit: "16kb" }));

app.get("/health", async (_request, response) => {
  try {
    await pool.execute("SELECT 1");
    response.json({ status: "ok", database: "connected" });
  } catch {
    response.status(503).json({ status: "unavailable", database: "disconnected" });
  }
});

app.use("/api/auth", authRoutes);
app.use("/api/account", requireAuth, accountRoutes);
app.use("/api/pix", requireAuth, pixRoutes);

app.use((request, _response, next) => {
  next(new HttpError(404, `Rota não encontrada: ${request.method} ${request.path}`));
});

app.use((error, _request, response, _next) => {
  if (error.code === "ER_DUP_ENTRY") {
    return response.status(409).json({ error: "E-mail, CPF ou chave PIX já cadastrado." });
  }

  if (error.status) {
    return response.status(error.status).json({ error: error.message });
  }

  console.error(error);
  return response.status(500).json({ error: "Ocorreu um erro interno. Tente novamente." });
});

let server;

async function start() {
  await ensureCounterpartySchema();
  server = app.listen(port, "0.0.0.0", () => {
    console.log(`UniPay API pronta na porta ${port}.`);
  });
}

start().catch((error) => {
  console.error("Não foi possível preparar o banco do UniPay.", error);
  process.exit(1);
});

async function shutdown() {
  if (!server) {
    await pool.end();
    process.exit(0);
    return;
  }
  server.close(async () => {
    await pool.end();
    process.exit(0);
  });
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
