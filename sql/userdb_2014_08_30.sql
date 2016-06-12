
CREATE TABLE `tb_elitescene` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `cid` int(10) unsigned NOT NULL,
      `free_fight` tinyint(3) unsigned DEFAULT NULL,
      `buyed_fight` tinyint(3) unsigned DEFAULT NULL,
      `left_buy_fight` tinyint(3) unsigned DEFAULT NULL,
      `last_datetime` datetime DEFAULT NULL,
      PRIMARY KEY (`id`),
      KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin




