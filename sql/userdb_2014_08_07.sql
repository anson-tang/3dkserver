ALTER TABLE `tb_bag_equip` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_bag_equipshard` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_bag_fellowsoul` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_bag_item` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_bag_treasure` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_bag_treasureshard` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;
ALTER TABLE `tb_fellow` CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NULL DEFAULT 0  ;


ALTER TABLE `tb_fellow` ADD COLUMN `deleted` TINYINT(4) UNSIGNED NULL  AFTER `camp_id` , ADD COLUMN `create_time` DATETIME NULL  AFTER `deleted` , ADD COLUMN `update_time` DATETIME NULL  AFTER `create_time` , ADD COLUMN `del_time` DATETIME NULL  AFTER `update_time` ;

ALTER TABLE `tb_bag_equip` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_equipshard` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_fellowsoul` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_item` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_normal` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_treasure` CHANGE COLUMN `create_time` `create_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `update_time` `update_time` DATETIME NULL DEFAULT NULL  , CHANGE COLUMN `del_time` `del_time` DATETIME NULL DEFAULT NULL  ;

ALTER TABLE `tb_bag_normal` CHANGE COLUMN `count` `count` INT(10) UNSIGNED NOT NULL  , CHANGE COLUMN `deleted` `deleted` TINYINT(4) UNSIGNED NOT NULL  , RENAME TO  `tb_bag_treasureshard` ;



ALTER TABLE `tb_bag_treasureshard` CHANGE COLUMN `count` `item_num` INT(10) UNSIGNED NOT NULL ;

