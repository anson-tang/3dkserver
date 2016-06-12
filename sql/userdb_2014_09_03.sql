
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin


