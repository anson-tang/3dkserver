
CREATE TABLE `tb_bag_equip` (
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

CREATE TABLE `tb_bag_equipshard` (
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

ALTER TABLE `tb_bag_equip` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_type` `item_type` SMALLINT(5) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_id` `item_id` INT(10) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_num` `item_num` INT(10) UNSIGNED NULL DEFAULT NULL  , ADD COLUMN `level` SMALLINT(5) UNSIGNED NULL  AFTER `item_num` , ADD COLUMN `refine_attribute` BLOB NULL  AFTER `level` ;

ALTER TABLE `tb_bag_treasure` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_type` `item_type` SMALLINT(5) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_id` `item_id` INT(10) UNSIGNED NULL DEFAULT NULL  , CHANGE COLUMN `item_num` `item_num` INT(10) UNSIGNED NULL DEFAULT NULL  , ADD COLUMN `level` SMALLINT(5) UNSIGNED NULL  AFTER `item_num` , ADD COLUMN `exp` INT(10) UNSIGNED NULL  AFTER `level` , ADD COLUMN `refine_level` SMALLINT(5) UNSIGNED NULL  AFTER `exp` ;



