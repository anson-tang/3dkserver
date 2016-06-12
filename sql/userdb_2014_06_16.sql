delimiter $$

CREATE TABLE `tb_bag_normal` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cid` int(10) unsigned NOT NULL,
  `item_type` smallint(5) unsigned NOT NULL,
  `item_id` bigint(20) unsigned NOT NULL,
  `count` int(10) NOT NULL,
  `deleted` tinyint(4) NOT NULL,
  `create_time` int(10) NOT NULL,
  `update_time` int(10) NOT NULL,
  `del_time` int(10) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `k_item_type` (`item_type`),
  KEY `k_item_id` (`item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_bin $$

delimiter ;