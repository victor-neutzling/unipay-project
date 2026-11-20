CREATE DATABASE IF NOT EXISTS uniPay
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE uniPay;

CREATE TABLE IF NOT EXISTS tipo_transacao (
  idTipoTransacao INT PRIMARY KEY AUTO_INCREMENT,
  tipo VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categoria (
  idCategoria INT PRIMARY KEY AUTO_INCREMENT,
  tipo VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS usuario (
  idUsuario INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  cpf VARCHAR(11) NOT NULL UNIQUE,
  senha VARCHAR(255) NOT NULL,
  saldo DECIMAL(20, 2) NOT NULL DEFAULT 0.00,
  criadoEm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chave_pix (
  idChavePix INT PRIMARY KEY AUTO_INCREMENT,
  idUsuario INT NOT NULL UNIQUE,
  chavePix VARCHAR(60) NOT NULL UNIQUE,
  FOREIGN KEY (idUsuario) REFERENCES usuario (idUsuario)
);

CREATE TABLE IF NOT EXISTS pix_recente (
  idPixRecente INT PRIMARY KEY AUTO_INCREMENT,
  idUsuario INT NOT NULL,
  idChavePix INT NOT NULL,
  criadoEm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_pix_recente_usuario_chave (idUsuario, idChavePix),
  FOREIGN KEY (idUsuario) REFERENCES usuario (idUsuario),
  FOREIGN KEY (idChavePix) REFERENCES chave_pix (idChavePix)
);

CREATE TABLE IF NOT EXISTS contraparte (
  idContraparte INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(255) NOT NULL,
  cpf VARCHAR(11) NULL,
  idUsuario INT NULL,
  tipo VARCHAR(30) NOT NULL,
  FOREIGN KEY (idUsuario) REFERENCES usuario (idUsuario)
);

CREATE TABLE IF NOT EXISTS transacao (
  idTransacao INT PRIMARY KEY AUTO_INCREMENT,
  idUsuario INT NOT NULL,
  idCategoria INT NOT NULL,
  idContraparte INT NOT NULL,
  valor DECIMAL(20, 2) NOT NULL,
  data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  idTipoTransacao INT NOT NULL,
  INDEX ix_transacao_usuario_data (idUsuario, data),
  FOREIGN KEY (idUsuario) REFERENCES usuario (idUsuario),
  FOREIGN KEY (idCategoria) REFERENCES categoria (idCategoria),
  FOREIGN KEY (idContraparte) REFERENCES contraparte (idContraparte),
  FOREIGN KEY (idTipoTransacao) REFERENCES tipo_transacao (idTipoTransacao),
  CONSTRAINT chk_transacao_valor_positivo CHECK (valor > 0)
);
