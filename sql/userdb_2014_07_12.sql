
ALTER TABLE `tb_fellow` ADD COLUMN `camp_id` TINYINT(4) NULL DEFAULT 0  AFTER `is_major` ;
ALTER TABLE `tb_bag_equip` ADD COLUMN `camp_id` TINYINT(4) NULL DEFAULT 0  AFTER `item_num` , ADD COLUMN `position_id` TINYINT(4) UNSIGNED NULL DEFAULT 0  AFTER `camp_id`;
ALTER TABLE `tb_bag_treasure` ADD COLUMN `camp_id` TINYINT(4) NULL DEFAULT 0  AFTER `item_num` , ADD COLUMN `position_id` TINYINT(4) UNSIGNED NULL DEFAULT 0  AFTER `camp_id` ;
ALTER TABLE `tb_fellow` CHANGE COLUMN `quality_level` `advanced_level` SMALLINT(6) NULL DEFAULT '0'  ;

