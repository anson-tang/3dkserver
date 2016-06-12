
CREATE TABLE `tb_activescene` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `cid` int(10) unsigned NOT NULL,
      `panda_free` tinyint(3) unsigned DEFAULT '0',
      `treasure_free` tinyint(3) unsigned DEFAULT '0',
      `treasure_buyed` tinyint(3) unsigned DEFAULT '0',
      `treasure_left_buy` tinyint(3) unsigned DEFAULT '0',
      `tree_free` tinyint(3) unsigned DEFAULT '0',
      `tree_buyed` tinyint(3) unsigned DEFAULT '0',
      `tree_left_buy` tinyint(3) unsigned DEFAULT '0',
      `last_datetime` datetime DEFAULT NULL,
      PRIMARY KEY (`id`),
      KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin



