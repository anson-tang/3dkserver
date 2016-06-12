ALTER TABLE `tb_bag_treasureshard` ADD COLUMN `aux_data` VARCHAR(512) NULL  AFTER `del_time` ;

ALTER TABLE `tb_bag_treasureshard` CHANGE COLUMN `aux_data` `aux_data` VARCHAR(512) CHARACTER SET 'utf8' COLLATE 'utf8_bin' NULL  ;


