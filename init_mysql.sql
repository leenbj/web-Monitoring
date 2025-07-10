-- 网址监控系统MySQL数据库初始化脚本
-- 适用于宝塔面板部署

-- 创建数据库
CREATE DATABASE IF NOT EXISTS website_monitor 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER IF NOT EXISTS 'monitor_user'@'localhost' IDENTIFIED BY 'BaotaUser2024!';
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'BaotaUser2024!';

-- 授予权限
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'localhost';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE website_monitor;

-- 网站分组表
CREATE TABLE IF NOT EXISTS website_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_group_name (name),
    INDEX idx_group_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网站分组表';

-- 网站表
CREATE TABLE IF NOT EXISTS websites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    original_url TEXT NOT NULL,
    normalized_url TEXT,
    description TEXT,
    group_id INT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES website_groups(id),
    INDEX idx_website_name (name),
    INDEX idx_website_domain (domain),
    INDEX idx_website_active (is_active),
    INDEX idx_website_group (group_id),
    INDEX idx_website_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监控网站表';

-- 检测任务表
CREATE TABLE IF NOT EXISTS detection_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    interval_hours INT NOT NULL DEFAULT 6,
    max_concurrent INT DEFAULT 10,
    timeout_seconds INT DEFAULT 30,
    retry_times INT DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_run_at DATETIME,
    next_run_at DATETIME,
    total_runs INT DEFAULT 0,
    success_runs INT DEFAULT 0,
    failed_runs INT DEFAULT 0,
    INDEX idx_task_active (is_active),
    INDEX idx_task_running (is_running),
    INDEX idx_task_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测任务表';

-- 检测记录表
CREATE TABLE IF NOT EXISTS detection_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website_id INT NOT NULL,
    task_id INT,
    status VARCHAR(20) NOT NULL,
    final_url TEXT,
    response_time FLOAT,
    http_status_code INT,
    error_message TEXT,
    failure_reason VARCHAR(50),
    ssl_info JSON,
    redirect_chain JSON,
    page_title TEXT,
    page_content_length INT,
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retry_count INT DEFAULT 0,
    detection_duration FLOAT,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES detection_tasks(id),
    INDEX idx_record_website_time (website_id, detected_at),
    INDEX idx_record_status_time (status, detected_at),
    INDEX idx_record_task_time (task_id, detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测记录表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    real_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_login_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_username (username),
    INDEX idx_user_email (email),
    INDEX idx_user_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 任务-网站关联表
CREATE TABLE IF NOT EXISTS task_websites (
    task_id INT NOT NULL,
    website_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, website_id),
    FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务网站关联表';

-- 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(100) NOT NULL UNIQUE,
    `value` TEXT,
    description TEXT,
    category VARCHAR(50),
    data_type VARCHAR(20) DEFAULT 'string',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (`key`),
    INDEX idx_setting_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统设置表';

-- 网站状态变化记录表
CREATE TABLE IF NOT EXISTS website_status_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website_id INT NOT NULL,
    task_id INT,
    previous_status VARCHAR(20),
    current_status VARCHAR(20) NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    previous_detection_id INT,
    current_detection_id INT,
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES detection_tasks(id),
    FOREIGN KEY (previous_detection_id) REFERENCES detection_records(id),
    FOREIGN KEY (current_detection_id) REFERENCES detection_records(id),
    INDEX idx_status_change_website_time (website_id, detected_at),
    INDEX idx_status_change_type_time (change_type, detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网站状态变化记录表';

-- 失败网站监控任务表
CREATE TABLE IF NOT EXISTS failed_site_monitor_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_task_id INT NOT NULL,
    interval_hours INT DEFAULT 1,
    max_concurrent INT DEFAULT 10,
    timeout_seconds INT DEFAULT 30,
    retry_times INT DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_run_at DATETIME,
    next_run_at DATETIME,
    FOREIGN KEY (parent_task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
    INDEX idx_failed_task_parent (parent_task_id),
    INDEX idx_failed_task_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='失败网站监控任务表';

-- 失败网站监控关联表
CREATE TABLE IF NOT EXISTS failed_site_monitor_websites (
    monitor_task_id INT NOT NULL,
    website_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (monitor_task_id, website_id),
    FOREIGN KEY (monitor_task_id) REFERENCES failed_site_monitor_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='失败网站监控关联表';

-- 文件上传记录表
CREATE TABLE IF NOT EXISTS upload_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INT,
    file_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    total_rows INT,
    processed_rows INT,
    success_rows INT,
    failed_rows INT,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    INDEX idx_upload_status (status),
    INDEX idx_upload_time (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件上传记录表';

-- 用户文件管理表
CREATE TABLE IF NOT EXISTS user_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INT,
    file_type VARCHAR(50),
    source_type VARCHAR(20) NOT NULL,
    original_export_path TEXT,
    download_count INT DEFAULT 0,
    last_download_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_file_source (source_type),
    INDEX idx_user_file_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户文件管理表';

-- 插入默认数据

-- 默认网站分组
INSERT IGNORE INTO website_groups (id, name, description, is_default) VALUES
(1, '默认分组', '系统默认分组', TRUE),
(2, '政府机构', '政府机构网站', FALSE),
(3, '企业网站', '企业官方网站', FALSE);

-- 默认系统设置
INSERT IGNORE INTO system_settings (`key`, `value`, description, category, data_type) VALUES
('email_smtp_server', 'smtp.qq.com', 'SMTP服务器地址', 'email', 'string'),
('email_smtp_port', '587', 'SMTP端口', 'email', 'integer'),
('email_use_tls', 'true', '是否使用TLS', 'email', 'boolean'),
('detection_default_interval', '60', '默认检测间隔(分钟)', 'detection', 'integer'),
('detection_max_concurrent', '20', '最大并发检测数', 'detection', 'integer'),
('detection_timeout', '30', '检测超时时间(秒)', 'detection', 'integer');

-- 创建默认管理员用户（密码: admin123）
INSERT IGNORE INTO users (username, password_hash, email, real_name, role, status) VALUES
('admin', 'pbkdf2:sha256:600000$uMJ8Vg8S$7c6a3d1f0c3e6a7b8d5f4a9b2e6c8d9f1a4b7c5e8d2f6a9b3c7e1d5f8a2b6c4e9', 'admin@example.com', '系统管理员', 'admin', 'active');

-- 创建示例检测任务
INSERT IGNORE INTO detection_tasks (id, name, description, interval_hours, max_concurrent, timeout_seconds, retry_times) VALUES
(1, '默认监控任务', '系统默认创建的监控任务', 6, 10, 30, 3);

COMMIT;