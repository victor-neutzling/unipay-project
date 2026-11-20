USE uniPay;

SET @has_counterparty_cpf = (
  SELECT COUNT(*)
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'contraparte'
     AND COLUMN_NAME = 'cpf'
);
SET @add_counterparty_cpf = IF(
  @has_counterparty_cpf = 0,
  'ALTER TABLE contraparte ADD COLUMN cpf VARCHAR(11) NULL AFTER nome',
  'SELECT 1'
);
PREPARE counterparty_cpf_stmt FROM @add_counterparty_cpf;
EXECUTE counterparty_cpf_stmt;
DEALLOCATE PREPARE counterparty_cpf_stmt;

UPDATE contraparte AS cp
JOIN usuario AS u ON u.idUsuario = cp.idUsuario
   SET cp.cpf = u.cpf
 WHERE cp.cpf IS NULL;
