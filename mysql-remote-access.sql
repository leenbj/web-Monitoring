-- 宝塔面板MySQL远程连接配置
-- 在宝塔面板的phpMyAdmin中执行

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS website_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户并授权（允许从Docker容器IP访问）
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'localhost' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'172.%' IDENTIFIED BY 'BaotaUser2024!';

-- 3. 授予权限
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'localhost';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'172.%';

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 5. 检查用户权限
SELECT host, user FROM mysql.user WHERE user = 'monitor_user';

-- 6. 检查数据库权限
SHOW GRANTS FOR 'monitor_user'@'%';

-- 7. 检查数据库是否存在
SHOW DATABASES LIKE 'website_monitor';