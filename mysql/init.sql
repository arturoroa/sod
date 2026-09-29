CREATE DATABASE IF NOT EXISTS sod;

CREATE USER IF NOT EXISTS 'appuser'@'%' IDENTIFIED BY 'apppass';
GRANT ALL PRIVILEGES ON *.* TO 'appuser'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS sod.users (
  UserID VARCHAR(100) NOT NULL PRIMARY KEY,
  Password VARCHAR(255) NOT NULL,
  UserType VARCHAR(50) NOT NULL,
  Company VARCHAR(100) NOT NULL,
  Email VARCHAR(255) NULL,
  Phone VARCHAR(100) NULL,
  Active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sod.Original_SOD_Rule_Set (
  `Ruleset Name` TEXT NULL,
  `Is Default Ruleset` TINYINT(1) NULL,
  `Risk Id` BIGINT NULL,
  `Enabled` TINYINT(1) NULL,
  `Name` TEXT NULL,
  `Description` TEXT NULL,
  `Risk Type` TEXT NULL,
  `Business Cycle` TEXT NULL,
  `Business Process` TEXT NULL,
  `Security Object Label` TEXT NULL,
  `Security Object Name` TEXT NULL,
  `Security Object Type` TEXT NULL,
  `Product` TEXT NULL,
  `Policy` DOUBLE NULL,
  `Risk Level` TEXT NULL,
  `Default Mitigation` TINYINT(1) NULL,
  `Mitigation Status` DOUBLE NULL,
  `Mitigation` DOUBLE NULL,
  `Mitigation Notes` DOUBLE NULL
);

INSERT INTO sod.users (UserID, Password, UserType, Company, Email, Phone, Active)
VALUES (
  'aroa',
  'scrypt:32768:8:1$84MqLevdk5E9dCtz$c2f782a21c82b45904145cfec46776f85a8c2c029355fe24384d1695803ba553d74ac900ea28d8a5c0a9443b1e5574418cc54d21399e10322ec4a77c4ad8ba23',
  'admin',
  'local',
  'aroa@local.test',
  '0000000000',
  1
)
ON DUPLICATE KEY UPDATE
  Password = VALUES(Password),
  UserType = VALUES(UserType),
  Company = VALUES(Company),
  Email = VALUES(Email),
  Phone = VALUES(Phone),
  Active = VALUES(Active);

-- este usuario usa la contraseña: !Qaz2wsx
-- la tabla Original_SOD_Rule_Set es requerida por el login para crear local.SOD_Rules
