ALTER TABLE `tb_character` ADD COLUMN `total_cost` INT(10) UNSIGNED NULL DEFAULT 0  AFTER `credits_payed` , ADD COLUMN `last_login_time` DATETIME NULL  AFTER `register_time` ;

