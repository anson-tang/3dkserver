
CREATE TABLE `tb_scene` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `cid` int(10) unsigned DEFAULT NULL,
      `scene_id` int(10) unsigned DEFAULT NULL,
      `dungeon_id` int(10) unsigned DEFAULT NULL,
      `dungeon_star` tinyint(3) unsigned DEFAULT '0',
      `dungeon_today_count` smallint(5) unsigned DEFAULT '0',
      `dungeon_last_time` int(10) unsigned DEFAULT '0',
      PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;



