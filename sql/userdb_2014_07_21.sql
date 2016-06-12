ALTER TABLE `tb_character` DROP COLUMN `skill_ball_count` , DROP COLUMN `server_time` , DROP COLUMN `sex` , ADD COLUMN `credits_payed` INT NULL DEFAULT 0  AFTER `credits` ;
