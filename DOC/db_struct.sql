-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Creato il: Mar 05, 2026 alle 11:33
-- Versione del server: 8.0.27
-- Versione PHP: 7.3.31-1~deb10u7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `p2pdev`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `Admins`
--

CREATE TABLE `Admins` (
  `email` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Aule`
--

CREATE TABLE `Aule` (
  `idA` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Lezioni`
--

CREATE TABLE `Lezioni` (
  `matricolaP` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ora` int NOT NULL,
  `data` date NOT NULL,
  `matricolaT` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `materiaL` varchar(3) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `argomenti` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `validata` int DEFAULT '0',
  `aulaL` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `svolta` int DEFAULT '0',
  `lastUpdate` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `google_calendar_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `LezioniCancellate`
--

CREATE TABLE `LezioniCancellate` (
  `matricolaP` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ora` int NOT NULL,
  `data` date NOT NULL,
  `matricolaT` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `materiaL` varchar(3) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `argomenti` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `validata` int NOT NULL DEFAULT '0',
  `aulaL` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `svolta` int NOT NULL DEFAULT '0',
  `deleteDateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleter` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `LezioniTutorRimossi`
--

CREATE TABLE `LezioniTutorRimossi` (
  `matricolaP` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ora` int NOT NULL,
  `data` date NOT NULL,
  `matricolaT` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `materiaL` varchar(3) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `argomenti` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `validata` int DEFAULT '0',
  `aulaL` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Materie`
--

CREATE TABLE `Materie` (
  `idMat` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `MaterieInsegnate`
--

CREATE TABLE `MaterieInsegnate` (
  `idMat` varchar(4) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `matricola` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Peer`
--

CREATE TABLE `Peer` (
  `matricolaP` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `descrizione` varchar(500) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Studenti`
--

CREATE TABLE `Studenti` (
  `cognome` varchar(40) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `nome` varchar(40) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `data_nascita` varchar(12) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `matricola` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `classe` varchar(6) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(35) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `emailgenitore1` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `emailgenitore2` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `abilitato` int DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `Tutorati`
--

CREATE TABLE `Tutorati` (
  `matricolaT` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `ConfigurazioneServizio`
--

CREATE TABLE `ConfigurazioneServizio` (
  `chiave` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `valore` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dati per la tabella `ConfigurazioneServizio`
--

INSERT INTO `ConfigurazioneServizio` (`chiave`, `valore`) VALUES
('versione', '1.0.0'),
('servizio_attivo', '1');

-- --------------------------------------------------------

--
-- Struttura della tabella `utentiws`
--

CREATE TABLE `utentiws` (
  `id` varchar(200) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `profile_pic` varchar(1000) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `ConfigurazioneServizio`
--
ALTER TABLE `ConfigurazioneServizio`
  ADD PRIMARY KEY (`chiave`);

--
-- Indici per le tabelle `Admins`
--
ALTER TABLE `Admins`
  ADD PRIMARY KEY (`email`);

--
-- Indici per le tabelle `Aule`
--
ALTER TABLE `Aule`
  ADD PRIMARY KEY (`idA`);

--
-- Indici per le tabelle `Lezioni`
--
ALTER TABLE `Lezioni`
  ADD PRIMARY KEY (`matricolaP`,`ora`,`data`),
  ADD KEY `matricolaT` (`matricolaT`),
  ADD KEY `materiaL` (`materiaL`),
  ADD KEY `aulaL` (`aulaL`);

--
-- Indici per le tabelle `LezioniCancellate`
--
ALTER TABLE `LezioniCancellate`
  ADD PRIMARY KEY (`deleteDateTime`,`deleter`);

--
-- Indici per le tabelle `Materie`
--
ALTER TABLE `Materie`
  ADD PRIMARY KEY (`idMat`);

--
-- Indici per le tabelle `MaterieInsegnate`
--
ALTER TABLE `MaterieInsegnate`
  ADD PRIMARY KEY (`idMat`,`matricola`),
  ADD KEY `matricolaP` (`matricola`);

--
-- Indici per le tabelle `Peer`
--
ALTER TABLE `Peer`
  ADD PRIMARY KEY (`matricolaP`);

--
-- Indici per le tabelle `Studenti`
--
ALTER TABLE `Studenti`
  ADD PRIMARY KEY (`matricola`);

--
-- Indici per le tabelle `Tutorati`
--
ALTER TABLE `Tutorati`
  ADD PRIMARY KEY (`matricolaT`);

--
-- Indici per le tabelle `utentiws`
--
ALTER TABLE `utentiws`
  ADD PRIMARY KEY (`id`);

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `Lezioni`
--
ALTER TABLE `Lezioni`
  ADD CONSTRAINT `Lezioni_ibfk_2` FOREIGN KEY (`matricolaT`) REFERENCES `Studenti` (`matricola`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `Lezioni_ibfk_3` FOREIGN KEY (`materiaL`) REFERENCES `Materie` (`idMat`),
  ADD CONSTRAINT `Lezioni_ibfk_4` FOREIGN KEY (`aulaL`) REFERENCES `Aule` (`idA`);

--
-- Limiti per la tabella `MaterieInsegnate`
--
ALTER TABLE `MaterieInsegnate`
  ADD CONSTRAINT `MaterieInsegnate_ibfk_1` FOREIGN KEY (`idMat`) REFERENCES `Materie` (`idMat`);

--
-- Limiti per la tabella `Peer`
--
ALTER TABLE `Peer`
  ADD CONSTRAINT `Peer_ibfk_1` FOREIGN KEY (`matricolaP`) REFERENCES `Studenti` (`matricola`);

--
-- Limiti per la tabella `Tutorati`
--
ALTER TABLE `Tutorati`
  ADD CONSTRAINT `Tutorati_ibfk_1` FOREIGN KEY (`matricolaT`) REFERENCES `Studenti` (`matricola`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
