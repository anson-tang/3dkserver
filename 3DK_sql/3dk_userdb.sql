-- MySQL dump 10.13  Distrib 5.5.47, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: 3dk_userdb
-- ------------------------------------------------------
-- Server version	5.5.47-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tb_activescene`
--

DROP TABLE IF EXISTS `tb_activescene`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_activescene` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `panda_free` tinyint(3) unsigned DEFAULT '0',
  `panda_buyed` tinyint(3) unsigned DEFAULT '0',
  `panda_left_buy` tinyint(3) unsigned DEFAULT '0',
  `treasure_free` tinyint(3) unsigned DEFAULT '0',
  `treasure_buyed` tinyint(3) unsigned DEFAULT '0',
  `treasure_left_buy` tinyint(3) unsigned DEFAULT '0',
  `tree_free` tinyint(3) unsigned DEFAULT '0',
  `tree_buyed` tinyint(3) unsigned DEFAULT '0',
  `tree_left_buy` tinyint(3) unsigned DEFAULT '0',
  `last_datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_atlaslist`
--

DROP TABLE IF EXISTS `tb_atlaslist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_atlaslist` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT NULL,
  `fellow_ids` blob,
  `equip_ids` blob,
  `treasure_ids` blob,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_equip`
--

DROP TABLE IF EXISTS `tb_bag_equip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_equip` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT '0',
  `item_type` smallint(5) unsigned DEFAULT NULL,
  `item_id` int(10) unsigned DEFAULT NULL,
  `item_num` int(10) unsigned DEFAULT NULL,
  `camp_id` tinyint(4) DEFAULT '0',
  `position_id` tinyint(4) unsigned DEFAULT '0',
  `level` smallint(5) unsigned DEFAULT NULL,
  `strengthen_cost` int(10) unsigned DEFAULT '0',
  `refine_cost` int(10) unsigned DEFAULT '0',
  `refine_attribute` blob,
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_equipshard`
--

DROP TABLE IF EXISTS `tb_bag_equipshard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_equipshard` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT '0',
  `item_type` smallint(5) DEFAULT NULL,
  `item_id` int(10) DEFAULT NULL,
  `item_num` int(10) DEFAULT NULL,
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_fellowsoul`
--

DROP TABLE IF EXISTS `tb_bag_fellowsoul`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_fellowsoul` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT '0',
  `item_type` smallint(5) DEFAULT NULL,
  `item_id` int(10) DEFAULT NULL,
  `item_num` int(10) DEFAULT NULL,
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_item`
--

DROP TABLE IF EXISTS `tb_bag_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_item` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT '0',
  `item_type` smallint(5) DEFAULT NULL,
  `item_id` int(10) DEFAULT NULL,
  `item_num` int(10) DEFAULT NULL,
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_jade`
--

DROP TABLE IF EXISTS `tb_bag_jade`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_jade` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT NULL,
  `item_type` smallint(5) unsigned DEFAULT NULL,
  `item_id` int(10) unsigned DEFAULT NULL,
  `item_num` int(10) unsigned DEFAULT NULL,
  `camp_id` tinyint(3) unsigned DEFAULT NULL,
  `position_id` tinyint(3) unsigned DEFAULT NULL,
  `level` smallint(5) unsigned DEFAULT NULL,
  `exp` int(10) unsigned DEFAULT NULL,
  `deleted` tinyint(3) unsigned DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_normal`
--

DROP TABLE IF EXISTS `tb_bag_normal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_normal` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `item_type` smallint(5) unsigned NOT NULL,
  `item_id` bigint(20) unsigned NOT NULL,
  `count` int(10) NOT NULL,
  `deleted` tinyint(4) NOT NULL,
  `create_time` int(10) NOT NULL,
  `update_time` int(10) NOT NULL,
  `del_time` int(10) NOT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `k_item_type` (`item_type`),
  KEY `k_item_id` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_treasure`
--

DROP TABLE IF EXISTS `tb_bag_treasure`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_treasure` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT '0',
  `item_type` smallint(5) unsigned DEFAULT NULL,
  `item_id` int(10) unsigned DEFAULT NULL,
  `item_num` int(10) unsigned DEFAULT '0',
  `camp_id` tinyint(4) DEFAULT '0',
  `position_id` tinyint(4) unsigned DEFAULT '0',
  `level` smallint(5) unsigned DEFAULT '0',
  `exp` int(10) unsigned DEFAULT '0',
  `refine_level` smallint(5) unsigned DEFAULT '0',
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_bag_treasureshard`
--

DROP TABLE IF EXISTS `tb_bag_treasureshard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_bag_treasureshard` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL DEFAULT '0',
  `item_type` smallint(5) unsigned NOT NULL,
  `item_id` bigint(20) unsigned NOT NULL,
  `item_num` int(10) unsigned NOT NULL,
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_character`
--

DROP TABLE IF EXISTS `tb_character`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_character` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `sid` int(10) NOT NULL DEFAULT '13',
  `account` varchar(128) COLLATE utf8_bin NOT NULL,
  `nick_name` varchar(32) COLLATE utf8_bin NOT NULL,
  `lead_id` int(10) unsigned NOT NULL DEFAULT '1',
  `level` int(10) unsigned NOT NULL DEFAULT '1',
  `exp` int(10) unsigned NOT NULL DEFAULT '0',
  `vip_level` int(10) unsigned NOT NULL DEFAULT '0',
  `might` int(10) unsigned NOT NULL DEFAULT '0',
  `recharge` int(10) NOT NULL DEFAULT '0',
  `golds` int(10) unsigned NOT NULL DEFAULT '0',
  `credits` bigint(20) unsigned NOT NULL DEFAULT '0',
  `credits_payed` int(11) unsigned DEFAULT '0',
  `total_cost` int(10) unsigned DEFAULT '0',
  `firstpay` tinyint(3) unsigned DEFAULT '0',
  `monthly_card` int(10) unsigned DEFAULT '0',
  `dual_monthly_card` int(10) DEFAULT NULL,
  `growth_plan` tinyint(3) unsigned DEFAULT '0',
  `register_time` datetime DEFAULT NULL,
  `last_login_time` datetime DEFAULT NULL,
  `fellow_capacity` smallint(6) unsigned NOT NULL DEFAULT '0',
  `item_capacity` smallint(6) unsigned NOT NULL DEFAULT '0',
  `treasure_capacity` smallint(6) unsigned NOT NULL DEFAULT '0',
  `equip_capacity` smallint(6) unsigned NOT NULL DEFAULT '0',
  `equipshard_capacity` smallint(6) unsigned NOT NULL DEFAULT '0',
  `jade_capacity` smallint(6) NOT NULL,
  `soul` int(10) unsigned NOT NULL DEFAULT '0',
  `hunyu` int(10) unsigned DEFAULT '0',
  `prestige` int(10) unsigned DEFAULT '0',
  `honor` int(10) DEFAULT NULL,
  `energy` smallint(5) unsigned DEFAULT '0',
  `chaos_level` smallint(5) unsigned DEFAULT '0',
  `scene_star` smallint(5) unsigned DEFAULT '0',
  `douzhan` int(10) unsigned DEFAULT '0',
  `tutorial_steps` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `friends` blob,
  `charge_ids` blob,
  PRIMARY KEY (`id`,`sid`),
  KEY `idx_nick_name` (`nick_name`) USING BTREE,
  KEY `idx_level` (`level`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_climbing_tower`
--

DROP TABLE IF EXISTS `tb_climbing_tower`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_climbing_tower` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `cur_layer` smallint(5) unsigned DEFAULT '0',
  `max_layer` smallint(5) unsigned DEFAULT '0',
  `free_reset` tinyint(3) unsigned DEFAULT '0',
  `buyed_reset` tinyint(3) unsigned DEFAULT '0',
  `left_buy_reset` tinyint(3) unsigned DEFAULT '0',
  `free_fight` tinyint(3) unsigned DEFAULT '0',
  `buyed_fight` tinyint(3) unsigned DEFAULT '0',
  `start_datetime` int(10) DEFAULT NULL,
  `last_datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_elitescene`
--

DROP TABLE IF EXISTS `tb_elitescene`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_elitescene` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `free_fight` tinyint(3) unsigned DEFAULT NULL,
  `buyed_fight` tinyint(3) unsigned DEFAULT NULL,
  `left_buy_fight` tinyint(3) unsigned DEFAULT NULL,
  `last_datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_fellow`
--

DROP TABLE IF EXISTS `tb_fellow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_fellow` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `fellow_id` int(10) NOT NULL,
  `level` int(11) DEFAULT '1',
  `exp` int(11) DEFAULT '0',
  `advanced_level` smallint(6) DEFAULT '0',
  `on_troop` tinyint(4) DEFAULT '0',
  `is_major` tinyint(4) DEFAULT '0',
  `camp_id` tinyint(4) DEFAULT '0',
  `deleted` tinyint(4) unsigned DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `del_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE,
  KEY `idx_deleted` (`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_goodwill`
--

DROP TABLE IF EXISTS `tb_goodwill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_goodwill` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned DEFAULT NULL,
  `fellow_id` int(10) unsigned DEFAULT NULL,
  `goodwill_exp` int(10) unsigned DEFAULT NULL,
  `goodwill_level` int(10) unsigned DEFAULT NULL,
  `last_gift` tinyint(3) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_payment`
--

DROP TABLE IF EXISTS `tb_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_payment` (
  `orderno` varchar(45) NOT NULL,
  `account` varchar(45) DEFAULT NULL,
  `cid` int(10) unsigned DEFAULT NULL,
  `server_id` varchar(45) DEFAULT NULL,
  `amount` varchar(45) DEFAULT NULL,
  `charge_id` varchar(45) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `get_credits` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`orderno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tb_scene`
--

DROP TABLE IF EXISTS `tb_scene`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tb_scene` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL DEFAULT '0',
  `scene_id` int(10) unsigned DEFAULT NULL,
  `dungeon_id` int(10) unsigned DEFAULT NULL,
  `dungeon_star` tinyint(3) unsigned DEFAULT '0',
  `dungeon_today_count` smallint(5) unsigned DEFAULT '0',
  `dungeon_award` int(10) DEFAULT '0',
  `dungeon_last_time` datetime DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`id`),
  KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-02-23 19:45:05
