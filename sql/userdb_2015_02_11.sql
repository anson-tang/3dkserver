CREATE  TABLE `tb_bag_jade` (
      `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
      `cid` INT(10) UNSIGNED NULL ,
      `item_type` SMALLINT(5) UNSIGNED NULL ,
      `item_id` INT(10) UNSIGNED NULL ,
      `item_num` INT(10) UNSIGNED NULL ,
      `camp_id` TINYINT(3) UNSIGNED NULL ,
      `position_id` TINYINT(3) UNSIGNED NULL ,
      `level` SMALLINT(5) UNSIGNED NULL ,
      `exp` INT(10) UNSIGNED NULL ,
      `deleted` TINYINT(3) UNSIGNED NULL ,
      `create_time` DATETIME NULL ,
      `update_time` DATETIME NULL ,
      `del_time` DATETIME NULL ,
      PRIMARY KEY (`id`) )
ENGINE = InnoDB DEFAULT CHARACTER SET = utf8 COLLATE = utf8_bin;

ALTER TABLE `tb_character` ADD COLUMN `jade_capacity` SMALLINT(5) UNSIGNED NOT NULL DEFAULT 150  AFTER `equipshard_capacity` ;


