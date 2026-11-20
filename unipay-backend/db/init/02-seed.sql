USE uniPay;

INSERT IGNORE INTO tipo_transacao (tipo) VALUES ('entrada'), ('saida');
INSERT IGNORE INTO categoria (tipo) VALUES ('PIX'), ('Outros');

-- Conta fixa usada pelos testes Selenium e pytest. O saldo de R$ 975 considera
-- o PIX de R$ 25 abaixo como já realizado.
-- O hash foi gerado com bcryptjs (12 rounds) para a senha teste@123.
INSERT IGNORE INTO usuario (nome, email, cpf, senha, saldo)
VALUES (
  'Usuario de Teste',
  'teste@email.com',
  '12345678909',
  '$2b$12$YfY0DpPcXdi2PysFdVfb4OG5zkozBTFZ1gJiQuINLeXs35WVPQlSi',
  975.00
);

-- Conta fixa que recebe os PIX dos testes Selenium.
-- O hash foi gerado com bcryptjs (12 rounds) para a senha destino@123.
INSERT IGNORE INTO usuario (nome, email, cpf, senha, saldo)
VALUES (
  'Destino Teste',
  'destino@email.com',
  '16899535009',
  '$2b$12$RrAxheb9UntWYfPIKZz7IOMWuMrsEyHcqsUK9vFpIrvzMTXrkxwau',
  0.00
);

SET @test_user_id = (SELECT idUsuario FROM usuario WHERE email = 'teste@email.com' LIMIT 1);

INSERT IGNORE INTO chave_pix (idUsuario, chavePix)
SELECT idUsuario, email FROM usuario
WHERE email = 'teste@email.com';

INSERT IGNORE INTO chave_pix (idUsuario, chavePix)
SELECT idUsuario, email FROM usuario
WHERE email = 'destino@email.com';

SET @pix_category_id = (SELECT idCategoria FROM categoria WHERE tipo = 'PIX' LIMIT 1);
SET @pix_out_id = (SELECT idTipoTransacao FROM tipo_transacao WHERE tipo = 'saida' LIMIT 1);

INSERT INTO contraparte (nome, cpf, idUsuario, tipo)
SELECT 'Destinatario Teste', '11144477735', NULL, 'pix'
WHERE NOT EXISTS (
  SELECT 1 FROM contraparte
  WHERE nome = 'Destinatario Teste'
    AND cpf = '11144477735'
    AND idUsuario IS NULL
    AND tipo = 'pix'
);
SET @outgoing_counterparty_id = (
  SELECT idContraparte FROM contraparte
  WHERE nome = 'Destinatario Teste'
    AND cpf = '11144477735'
    AND idUsuario IS NULL
    AND tipo = 'pix'
  ORDER BY idContraparte DESC LIMIT 1
);

INSERT INTO transacao (idUsuario, idCategoria, idContraparte, valor, data, idTipoTransacao)
SELECT @test_user_id, @pix_category_id, @outgoing_counterparty_id, 25.00, CURRENT_TIMESTAMP, @pix_out_id
WHERE NOT EXISTS (
  SELECT 1 FROM transacao
  WHERE idUsuario = @test_user_id
    AND idCategoria = @pix_category_id
    AND idContraparte = @outgoing_counterparty_id
    AND valor = 25.00
    AND idTipoTransacao = @pix_out_id
);
