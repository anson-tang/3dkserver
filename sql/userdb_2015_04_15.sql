ALTER TABLE `tb_character` ADD COLUMN `sid` SMALLINT(5) UNSIGNED NOT NULL DEFAULT 0 AFTER `id`, DROP PRIMARY KEY, ADD PRIMARY KEY (`id`, `sid`), ADD INDEX `idx_sid` USING BTREE (`id` ASC, `sid` ASC);

ALTER TABLE `tb_bag_jade` ADD INDEX `idx_deleted` USING BTREE (`cid` ASC, `deleted` ASC);

