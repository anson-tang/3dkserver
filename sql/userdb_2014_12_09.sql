CREATE  TABLE `tb_goodwill` (
      `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
      `cid` INT(10) UNSIGNED NULL ,
      `fellow_id` INT(10) UNSIGNED NULL ,
      `goodwill_exp` INT(10) UNSIGNED NULL ,
      `goodwill_level` INT(10) UNSIGNED NULL ,
      `last_gift` TINYINT(3) UNSIGNED NULL ,
      PRIMARY KEY (`id`) ,
      INDEX `idx_cid` USING BTREE (`cid` ASC) )
ENGINE = InnoDB DEFAULT CHARACTER SET = utf8 COLLATE = utf8_bin;


