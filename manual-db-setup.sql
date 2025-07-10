-- 手动数据库创建SQL脚本
-- 在MySQL中执行以下语句

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS website_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'localhost' IDENTIFIED BY 'BaotaUser2024!';

-- 3. 授权
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'localhost';

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 5. 验证创建结果
USE website_monitor;
SELECT 'Database created successfully' AS result;
SELECT User, Host FROM mysql.user WHERE User = 'monitor_user';