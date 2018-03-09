-- --------------------------------------------------------
-- Host:                         
-- Server version:               
-- Server OS:                    
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- Dumping structure for table monero_blockchain.header
CREATE TABLE IF NOT EXISTS `header` (
  `HASH` varchar(255) NOT NULL,
  `HEIGHT` bigint(11) NOT NULL,
  `DIFFICULTY` double NOT NULL,
  `MAJOR_VERSION` int(11) NOT NULL,
  `MINOR_VERSION` int(11) NOT NULL,
  `NONCE` double NOT NULL,
  `PREV_HASH` varchar(255) NOT NULL,
  `REWARD` double NOT NULL,
  `TIMESTAMP` double NOT NULL,
  PRIMARY KEY (`HASH`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.header_tx
CREATE TABLE IF NOT EXISTS `header_tx` (
  `TX_HASH` varchar(255) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `HEADER_HASH` varchar(255) NOT NULL,
  PRIMARY KEY (`TX_HASH`),
  KEY `TX_HASH_IDX_HEIGHT` (`TX_HASH`,`TX_IDX`,`HEADER_HEIGHT`),
  KEY `TX_HASH_IDX` (`TX_HASH`,`TX_IDX`),
  KEY `TX_IDX` (`TX_IDX`),
  KEY `TX_HEADERHEIGHT` (`HEADER_HEIGHT`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.height_test
CREATE TABLE IF NOT EXISTS `height_test` (
  `HEIGHT` int(11) NOT NULL,
  PRIMARY KEY (`HEIGHT`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.kimage_ringsize
CREATE TABLE IF NOT EXISTS `kimage_ringsize` (
  `K_IMAGE` varchar(255) NOT NULL,
  `RINGSIZE` int(11) NOT NULL,
  PRIMARY KEY (`K_IMAGE`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_io
CREATE TABLE IF NOT EXISTS `tx_io` (
  `TX_HASH` varchar(255) NOT NULL,
  `NUMINPUTS` int(11) NOT NULL,
  `NUMOUTPUTS` int(11) NOT NULL,
  PRIMARY KEY (`TX_HASH`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_vin
CREATE TABLE IF NOT EXISTS `tx_vin` (
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `TX_HASH` varchar(255) NOT NULL,
  `AMOUNT` double NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `KEY_OFFSETS` varchar(1000) NOT NULL,
  `VIN_IDX` int(11) NOT NULL,
  PRIMARY KEY (`K_IMAGE`),
  KEY `TXIN_TXHASH` (`TX_HASH`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_vin_mixin
CREATE TABLE IF NOT EXISTS `tx_vin_mixin` (
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `TX_HASH` varchar(255) NOT NULL,
  `VIN_IDX` int(11) NOT NULL,
  `MIXIN_IDX` int(11) NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `VOUT_KEY` varchar(255) NOT NULL,
  `VOUT_HEADER_HEIGHT` bigint(20) NOT NULL,
  PRIMARY KEY (`HEADER_HEIGHT`,`TX_HASH`,`MIXIN_IDX`,`K_IMAGE`,`VOUT_KEY`),
  KEY `TXVINMIXIN_TXHASH` (`TX_HASH`),
  KEY `TXVINMIXIN_VOUTKEY` (`VOUT_KEY`),
  KEY `TXVINMIXIN_HEADERHEIGHT` (`HEADER_HEIGHT`),
  KEY `TXVINMIXIN_KIMAGE` (`K_IMAGE`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_vin_mixin0
CREATE TABLE IF NOT EXISTS `tx_vin_mixin0` (
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `TX_HASH` varchar(255) NOT NULL,
  `VIN_IDX` int(11) NOT NULL,
  `MIXIN_IDX` int(11) NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `VOUT_KEY` varchar(255) NOT NULL,
  `VOUT_HEADER_HEIGHT` bigint(20) NOT NULL,
  KEY `TXVINMIXIN_TXHASH` (`TX_HASH`),
  KEY `TXVINMIXIN_VOUTKEY` (`VOUT_KEY`),
  KEY `TXVINMIXIN_HEADERHEIGHT` (`HEADER_HEIGHT`),
  KEY `TXVINMIXIN_KIMAGE` (`K_IMAGE`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_vin_mixin_hash
CREATE TABLE IF NOT EXISTS `tx_vin_mixin_hash` (
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `TX_HASH` varchar(255) NOT NULL,
  `VIN_IDX` int(11) NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `VOUT_KEY_HASH` varchar(255) NOT NULL,
  `VOUT_KEY_COUNT` int(11) NOT NULL,
  PRIMARY KEY (`K_IMAGE`,`VOUT_KEY_HASH`),
  KEY `TXVINMIXIN_TXHASH` (`TX_HASH`),
  KEY `TXVINMIXIN_VOUTKEY` (`VOUT_KEY_HASH`),
  KEY `TXVINMIXIN_HEADERHEIGHT` (`HEADER_HEIGHT`),
  KEY `TXVINMIXIN_KIMAGE` (`K_IMAGE`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.tx_vout
CREATE TABLE IF NOT EXISTS `tx_vout` (
  `HEADER_HEIGHT` bigint(20) NOT NULL,
  `TX_IDX` int(11) NOT NULL,
  `AMOUNT` double NOT NULL,
  `VOUT_KEY` varchar(255) NOT NULL,
  `TX_HASH` varchar(255) NOT NULL,
  `VOUT_IDX` int(11) NOT NULL,
  `VOUT_OFFSET` double NOT NULL,
  PRIMARY KEY (`VOUT_KEY`) USING BTREE,
  KEY `TX_VOUT_AMOUNT` (`AMOUNT`,`VOUT_OFFSET`) USING BTREE,
  KEY `TXOUT_VOUTKEY_AMOUNT_HEADERHEIGHT_TXIDX_VOUTIDX` (`VOUT_KEY`,`AMOUNT`,`HEADER_HEIGHT`,`TX_IDX`,`VOUT_IDX`) USING BTREE,
  KEY `TXOUT_HEADERHEIGHT` (`HEADER_HEIGHT`),
  KEY `TXOUT_TXIDX` (`TX_IDX`),
  KEY `TXOUT_VOUTIDX` (`VOUT_IDX`),
  KEY `TXOUT_TXHASH` (`TX_HASH`),
  KEY `TXOUT_VOUTOFFSET` (`VOUT_OFFSET`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.vin_amount_histogram
CREATE TABLE IF NOT EXISTS `vin_amount_histogram` (
  `AMOUNT` double NOT NULL,
  `OFFSET` double NOT NULL,
  PRIMARY KEY (`AMOUNT`),
  KEY `AMOUNTHISTOGRAM_AMOUNT_OFFSET` (`AMOUNT`,`OFFSET`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.voutkey_spent
CREATE TABLE IF NOT EXISTS `voutkey_spent` (
  `VOUT_KEY` varchar(255) NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `RINGSIZE` int(11) NOT NULL,
  `ITERATION` int(11) NOT NULL,
  PRIMARY KEY (`VOUT_KEY`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.voutkey_spent_dim
CREATE TABLE IF NOT EXISTS `voutkey_spent_dim` (
  `VOUT_KEY` varchar(255) NOT NULL,
  `K_IMAGE` varchar(255) NOT NULL,
  `RINGSIZE` int(11) NOT NULL,
  `ITERATION` int(11) NOT NULL,
  PRIMARY KEY (`VOUT_KEY`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.voutkey_usagecount
CREATE TABLE IF NOT EXISTS `voutkey_usagecount` (
  `VOUT_KEY` varchar(255) NOT NULL,
  `USAGECOUNT` int(11) NOT NULL,
  PRIMARY KEY (`VOUT_KEY`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
-- Dumping structure for table monero_blockchain.vout_amount_histogram
CREATE TABLE IF NOT EXISTS `vout_amount_histogram` (
  `AMOUNT` double NOT NULL,
  `OFFSET` double NOT NULL,
  PRIMARY KEY (`AMOUNT`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
