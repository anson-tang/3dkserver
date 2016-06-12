
CREATE TABLE `tb_payment` (
      `orderno` varchar(45) NOT NULL,
      `account` varchar(45) DEFAULT NULL,
      `cid` int(10) unsigned DEFAULT NULL,
      `server_id` varchar(45) DEFAULT NULL,
      `amount` varchar(45) DEFAULT NULL,
      `charge_id` varchar(45) DEFAULT NULL,
      `create_time` datetime DEFAULT NULL,
      `update_time` datetime DEFAULT NULL,
      `get_credits` int(10) unsigned DEFAULT NULL,
      PRIMARY KEY (`orderno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8




