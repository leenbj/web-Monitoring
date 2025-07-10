-- 网址监控系统 - 完整后端MySQL配置
-- 在宝塔面板的phpMyAdmin中执行，或通过mysql命令行执行

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS website_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户并设置密码
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'localhost' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'127.0.0.1' IDENTIFIED BY 'BaotaUser2024!';

-- 3. 授予完整权限
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'localhost';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'127.0.0.1';

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 5. 验证数据库和用户
SELECT 'Database created' AS status;
SHOW DATABASES LIKE 'website_monitor';

SELECT 'Users created' AS status;
SELECT host, user FROM mysql.user WHERE user = 'monitor_user';

SELECT 'Privileges granted' AS status;
SHOW GRANTS FOR 'monitor_user'@'%';

-- 6. 测试连接（可选）
USE website_monitor;
SELECT 'Database access test passed' AS test_result;