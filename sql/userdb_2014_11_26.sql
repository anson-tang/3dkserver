ALTER TABLE `tb_character` 
ADD INDEX `idx_nick_name` USING BTREE (`nick_name` ASC) 
, ADD INDEX `idx_level` USING BTREE (`level` ASC) ;



