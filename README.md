
mysql
===========================

Install
---------------------------

Create db and init
---------------------------
$ mysql -uroot -p
abcd.1234
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
mysql> create database 3dk_userdb character set utf8 collate utf8_bin;
Query OK, 1 row affected (0.04 sec)

mysql> create database 3dk_sysconfigdb character set utf8 collate utf8_bin;
Query OK, 1 row affected (0.00 sec)

mysql> create user '3dk-server'@'%' identified by '3dk-0#Ser.ver';
Query OK, 0 rows affected (0.00 sec)

mysql> grant all privileges on 3dk_userdb.* to '3dk-server'@'%' identified by '3dk-0#Ser.ver';
Query OK, 0 rows affected, 1 warning (0.00 sec)

mysql> grant all privileges on 3dk_sysconfigdb.* to '3dk-server'@'%';
Query OK, 0 rows affected (0.00 sec)

mysql> flush privileges;
Query OK, 0 rows affected (0.00 sec)
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| 3dk_sysconfigdb    |
| 3dk_userdb         |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
8 rows in set (0.00 sec)


$ mysql -u3dk-server -p -P13306 -h127.0.0.1 3dk_userdb < 3DK_sql/3dk_userdb.sql 
Enter password: 3dk-0#Ser.ver
$ mysql -u3dk-server -p -P13306 -h127.0.0.1 3dk_sysconfigdb < 3DK_sql/3dk_sysconfig.sql 
Enter password: 3dk-0#Ser.ver


restart server
=======================
1) ./stop_real

2) ./start



run a mysql-docker 
=======================
GENERATED ROOT PASSWORD: DEk23kSYzNEdsaf]Ab=4jyrARuN
1) docker run --name common-mysql -p 13306:3306 -v /root/workspace/backup/common-mysql/:/var/lib/mysql -e MYSQL_RANDOM_ROOT_PASSWORD=yes -e MYSQL_ONETIME_PASSWORD=yes -d mysql/mysql-server:5.5
2) docker run --name common-mysql -p 13306:3306 -v /root/workspace/backup/common-mysql/:/var/lib/mysql -e MYSQL_ROOT_PASSWORD= -d mysql/mysql-server:5.5
