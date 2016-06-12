ALTER TABLE `tb_character` ADD COLUMN `item_capacity` SMALLINT(6) NOT NULL DEFAULT 0  AFTER `fellow_capacity` , ADD COLUMN `treasure_capacity` SMALLINT(6) NOT NULL DEFAULT 0  AFTER `item_capacity` , ADD COLUMN `equip_capacity` SMALLINT(6) NOT NULL DEFAULT 0  AFTER `treasure_capacity` , ADD COLUMN `equipshard_capacity` SMALLINT(6) NOT NULL DEFAULT 0  AFTER `equip_capacity` ;

CREATE TABLE `tb_bag_item` (
      `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
      `cid` int(10) DEFAULT NULL,
      `item_type` SMALLINT(5) DEFAULT NULL,
      `item_id` INT(10) DEFAULT NULL,
      `item_num` INT(10) DEFAULT NULL,
      `deleted` TINYINT(4) DEFAULT NULL,
      `create_time` INT(10) DEFAULT NULL,
      `update_time` INT(10) DEFAULT NULL,
      `del_time` INT(10) DEFAULT NULL,
      `aux_data` VARCHAR(512) COLLATE utf8_bin DEFAULT NULL,
      PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `tb_bag_treasure` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `cid` int(10) DEFAULT NULL,
      `item_type` smallint(5) DEFAULT NULL,
      `item_id` int(10) DEFAULT NULL,
      `item_num` int(10) DEFAULT NULL,
      `deleted` tinyint(4) DEFAULT NULL,
      `create_time` int(10) DEFAULT NULL,
      `update_time` int(10) DEFAULT NULL,
      `del_time` int(10) DEFAULT NULL,
      `aux_data` varchar(512) COLLATE utf8_bin DEFAULT NULL,
      PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

