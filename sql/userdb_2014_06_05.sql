delimiter $$

alter table tb_character add `fellow_capacity` smallint(6) NOT NULL DEFAULT '0' $$

alter table tb_fellow add `level` int(10) DEFAULT '1' $$
alter table tb_fellow add `exp` int(10) DEFAULT '0' $$
alter table tb_fellow add `quality_level` smallint(6) DEFAULT '0' $$
alter table tb_fellow add `on_troop` tinyint(4) DEFAULT '0' $$
alter table tb_fellow add `is_major` tinyint(4) DEFAULT '0' $$

delimiter ;