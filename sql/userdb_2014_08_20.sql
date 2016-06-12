ALTER TABLE `tb_fellow` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NOT NULL  
, DROP INDEX `k_cid` 
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_scene` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NOT NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) ;

ALTER TABLE `tb_character` 
DROP INDEX `k_exp` 
, DROP INDEX `k_userid` 
, DROP INDEX `k_nick` ;

ALTER TABLE `tb_bag_equip` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_bag_equipshard` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC)
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_bag_fellowsoul` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_bag_item` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_bag_treasure` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NULL DEFAULT 0  
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;

ALTER TABLE `tb_bag_treasureshard` CHANGE COLUMN `cid` `cid` INT(10) UNSIGNED NOT NULL DEFAULT 0  
, DROP INDEX `k_item_type` 
, ADD INDEX `idx_cid` USING BTREE (`cid` ASC) 
, DROP INDEX `k_item_id` 
, ADD INDEX `idx_deleted` USING BTREE (`deleted` ASC) ;



