CREATE TABLE `tb_atlaslist` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `cid` int(10) unsigned DEFAULT NULL,
      `fellow_ids` blob,
      `equip_ids` blob,
      `treasure_ids` blob,
      PRIMARY KEY (`id`),
      KEY `idx_cid` (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin;




