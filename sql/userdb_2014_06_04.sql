delimiter $$

CREATE TABLE `tb_character` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `account` varchar(128) COLLATE utf8_bin NOT NULL,
  `nick_name` varchar(32) COLLATE utf8_bin NOT NULL,
  `lead_id` int(10) NOT NULL DEFAULT '1',
  `level` int(10) NOT NULL DEFAULT '1',
  `exp` int(10) NOT NULL DEFAULT '0',
  `vip_level` int(10) NOT NULL DEFAULT '0',
  `sex` int(10) NOT NULL DEFAULT '0' COMMENT '0:female, 1:male',
  `might` int(10) NOT NULL DEFAULT '0',
  `recharge` int(10) NOT NULL DEFAULT '0',
  `golds` int(10) NOT NULL DEFAULT '0',
  `credits` bigint(20) NOT NULL DEFAULT '0',
  `register_time` int(10) NOT NULL DEFAULT '0',
  `server_time` int(10) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `k_nick` (`nick_name`) USING HASH,
  UNIQUE KEY `k_userid` (`account`),
  KEY `k_exp` (`exp`)
) ENGINE=InnoDB AUTO_INCREMENT=50344 DEFAULT CHARSET=utf8 COLLATE=utf8_bin$$

CREATE TABLE `tb_fellow` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) NOT NULL,
  `fellow_id` int(10) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `k_cid` (`cid`)
) ENGINE=InnoDB AUTO_INCREMENT=10146 DEFAULT CHARSET=utf8 COLLATE=utf8_bin$$

delimiter ;
