CREATE  TABLE `tb_bag_fellowsoul` (
      `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
      `cid` INT(10) NULL ,
      `item_type` SMALLINT(5) NULL ,
      `item_id` INT(10) NULL ,
      `item_num` INT(10) NULL ,
      `deleted` TINYINT(4) NULL ,
      `create_time` INT(10) NULL ,
      `update_time` INT(10) NULL ,
      `del_time` INT(10) NULL ,
      `aux_data` VARCHAR(512) NULL ,
      PRIMARY KEY (`id`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8
COLLATE = utf8_bin;


