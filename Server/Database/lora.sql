-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Aug 22, 2017 at 06:51 PM
-- Server version: 5.7.19-0ubuntu0.16.04.1
-- PHP Version: 7.0.22-0ubuntu0.16.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `lora`
--

-- --------------------------------------------------------

--
-- Table structure for table `bandwidth`
--

CREATE TABLE `bandwidth` (
  `id` int(11) NOT NULL,
  `bandwidth` int(2) NOT NULL,
  `bandwidth_value` double NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Dumping data for table `bandwidth`
--

INSERT INTO `bandwidth` (`id`, `bandwidth`, `bandwidth_value`) VALUES
(1, 0, 7.8),
(2, 1, 10.4),
(3, 2, 15.6),
(4, 3, 20.8),
(5, 4, 31.25),
(6, 5, 41.7),
(7, 6, 62.5),
(8, 7, 125),
(9, 8, 250),
(10, 9, 500);

-- --------------------------------------------------------

--
-- Table structure for table `coding_rate`
--

CREATE TABLE `coding_rate` (
  `id` int(11) NOT NULL,
  `coding_rate` int(2) NOT NULL,
  `coding_rate_value` varchar(3) COLLATE utf8_slovenian_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Dumping data for table `coding_rate`
--

INSERT INTO `coding_rate` (`id`, `coding_rate`, `coding_rate_value`) VALUES
(1, 1, '4/5'),
(2, 2, '4/6'),
(3, 3, '4/7'),
(4, 4, '4/8');

-- --------------------------------------------------------

--
-- Table structure for table `frequency`
--

CREATE TABLE `frequency` (
  `id` int(11) NOT NULL,
  `frequency` int(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Dumping data for table `frequency`
--

INSERT INTO `frequency` (`id`, `frequency`) VALUES
(1, 868000000),
(2, 433000000);

-- --------------------------------------------------------

--
-- Table structure for table `measurements`
--

CREATE TABLE `measurements` (
  `id` int(11) NOT NULL,
  `sensor_id` int(11) NOT NULL,
  `rx_id` bigint(20) DEFAULT NULL,
  `current_rssi` double DEFAULT NULL,
  `packer_rssi` double DEFAULT NULL,
  `snr` double DEFAULT NULL,
  `timestamp` varchar(17) COLLATE utf8_slovenian_ci DEFAULT NULL,
  `crc_err_no` bigint(20) DEFAULT NULL,
  `packet_gsp_longitude` double DEFAULT NULL,
  `packet_gsp_latitude` double DEFAULT NULL,
  `additional_sensor_data` text COLLATE utf8_slovenian_ci,
  `status` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

-- --------------------------------------------------------

--
-- Table structure for table `point_time`
--

CREATE TABLE `point_time` (
  `id` int(11) NOT NULL,
  `point_number` int(11) NOT NULL,
  `timestamp` varchar(17) COLLATE utf8_slovenian_ci NOT NULL,
  `description` text COLLATE utf8_slovenian_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sensor`
--

CREATE TABLE `sensor` (
  `id` int(11) NOT NULL,
  `device_id` int(3) NOT NULL,
  `longitude` double NOT NULL,
  `latitude` double NOT NULL,
  `settings` int(11) NOT NULL,
  `receiver` tinyint(1) NOT NULL,
  `measurements_started_at` varchar(17) COLLATE utf8_slovenian_ci NOT NULL,
  `location_description` text COLLATE utf8_slovenian_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

-- --------------------------------------------------------

--
-- Table structure for table `settings`
--

CREATE TABLE `settings` (
  `id` int(11) NOT NULL,
  `frequency` double DEFAULT NULL,
  `bandwidth` int(2) DEFAULT NULL,
  `spreading_factor` int(2) DEFAULT NULL,
  `code_rate` int(11) DEFAULT NULL,
  `coding_rate_on` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

-- --------------------------------------------------------

--
-- Table structure for table `spreading_factor`
--

CREATE TABLE `spreading_factor` (
  `id` int(11) NOT NULL,
  `spreading_factor` int(2) NOT NULL,
  `spreading_factor_value` int(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Dumping data for table `spreading_factor`
--

INSERT INTO `spreading_factor` (`id`, `spreading_factor`, `spreading_factor_value`) VALUES
(1, 6, 64),
(2, 7, 128),
(3, 8, 256),
(4, 9, 512),
(5, 10, 1024),
(6, 11, 2048),
(7, 12, 4096);

-- --------------------------------------------------------

--
-- Table structure for table `status`
--

CREATE TABLE `status` (
  `id` int(11) NOT NULL,
  `status` varchar(100) COLLATE utf8_slovenian_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Dumping data for table `status`
--

INSERT INTO `status` (`id`, `status`) VALUES
(1, 'OK'),
(2, 'CRCERROR'),
(3, 'ERROR'),
(4, 'rxOnGoing'),
(5, 'signalDetected'),
(6, 'headerInfoValid');

-- --------------------------------------------------------

--
-- Table structure for table `travel_location`
--

CREATE TABLE `travel_location` (
  `id` int(11) NOT NULL,
  `lon` double DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `timestamp` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_slovenian_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bandwidth`
--
ALTER TABLE `bandwidth`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `coding_rate`
--
ALTER TABLE `coding_rate`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `frequency`
--
ALTER TABLE `frequency`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `measurements`
--
ALTER TABLE `measurements`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sensod_id` (`sensor_id`),
  ADD KEY `status` (`status`);

--
-- Indexes for table `point_time`
--
ALTER TABLE `point_time`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sensor`
--
ALTER TABLE `sensor`
  ADD PRIMARY KEY (`id`),
  ADD KEY `settings` (`settings`);

--
-- Indexes for table `settings`
--
ALTER TABLE `settings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id` (`id`),
  ADD KEY `code_rate` (`code_rate`),
  ADD KEY `spreading_factor` (`spreading_factor`),
  ADD KEY `banwidth` (`bandwidth`),
  ADD KEY `frequency` (`frequency`);

--
-- Indexes for table `spreading_factor`
--
ALTER TABLE `spreading_factor`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `status`
--
ALTER TABLE `status`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `travel_location`
--
ALTER TABLE `travel_location`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bandwidth`
--
ALTER TABLE `bandwidth`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;
--
-- AUTO_INCREMENT for table `coding_rate`
--
ALTER TABLE `coding_rate`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
--
-- AUTO_INCREMENT for table `frequency`
--
ALTER TABLE `frequency`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
--
-- AUTO_INCREMENT for table `measurements`
--
ALTER TABLE `measurements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=114062;
--
-- AUTO_INCREMENT for table `point_time`
--
ALTER TABLE `point_time`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;
--
-- AUTO_INCREMENT for table `sensor`
--
ALTER TABLE `sensor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;
--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;
--
-- AUTO_INCREMENT for table `spreading_factor`
--
ALTER TABLE `spreading_factor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;
--
-- AUTO_INCREMENT for table `status`
--
ALTER TABLE `status`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
--
-- AUTO_INCREMENT for table `travel_location`
--
ALTER TABLE `travel_location`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19729;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
