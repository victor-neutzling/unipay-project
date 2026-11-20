import mysql from "mysql2/promise";

export const pool = mysql.createPool({
  host: process.env.DB_HOST ?? "127.0.0.1",
  port: Number(process.env.DB_PORT ?? 3306),
  user: process.env.DB_USER ?? "unipay_app",
  password: process.env.DB_PASSWORD ?? "change-this-local-password",
  database: process.env.DB_NAME ?? "uniPay",
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  timezone: "Z",
  decimalNumbers: true,
  dateStrings: true,
});

export async function ensureCounterpartySchema() {
  const [rows] = await pool.execute(
    `SELECT COUNT(*) AS columnCount
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'contraparte'
        AND COLUMN_NAME = 'cpf'`,
  );
  if (Number(rows[0].columnCount) === 0) {
    await pool.execute("ALTER TABLE contraparte ADD COLUMN cpf VARCHAR(11) NULL AFTER nome");
  }
  await pool.execute(
    `UPDATE contraparte AS cp
       JOIN usuario AS u ON u.idUsuario = cp.idUsuario
        SET cp.cpf = u.cpf
      WHERE cp.cpf IS NULL`,
  );

  const [nameColumns] = await pool.execute(
    `SELECT CHARACTER_MAXIMUM_LENGTH AS nameLength
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'contraparte'
        AND COLUMN_NAME = 'nome'`,
  );
  if (Number(nameColumns[0]?.nameLength ?? 0) < 255) {
    await pool.execute("ALTER TABLE contraparte MODIFY COLUMN nome VARCHAR(255) NOT NULL");
  }
}

export async function withTransaction(callback) {
  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();
    const result = await callback(connection);
    await connection.commit();
    return result;
  } catch (error) {
    await connection.rollback();
    throw error;
  } finally {
    connection.release();
  }
}
