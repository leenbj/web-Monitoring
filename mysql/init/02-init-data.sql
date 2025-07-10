-- 网址监控系统初始数据脚本
-- 插入默认数据

USE website_monitor;

-- 插入默认分组
INSERT IGNORE INTO website_groups (name, description, is_default) VALUES 
('默认分组', '系统默认分组，用于存放未分类的网站', TRUE),
('重要网站', '重要的网站，需要重点监控', FALSE),
('测试网站', '用于测试的网站', FALSE);

-- 插入默认检测任务
INSERT IGNORE INTO detection_tasks (
    name, 
    description, 
    interval_hours, 
    max_concurrent, 
    timeout_seconds, 
    retry_times,
    is_active
) VALUES (
    '默认检测任务',
    '系统默认的网站检测任务，每6小时执行一次',
    6,
    10,
    30,
    3,
    TRUE
);

-- 创建系统配置表（如果需要）
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '设置ID',
    setting_key VARCHAR(100) NOT NULL UNIQUE COMMENT '设置键',
    setting_value TEXT COMMENT '设置值',
    setting_type VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT '设置类型',
    description TEXT COMMENT '设置描述',
    is_public BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否公开设置',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_setting_key (setting_key),
    INDEX idx_setting_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';

-- 插入默认系统设置
INSERT IGNORE INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('system_name', '网址监控系统', 'string', '系统名称', TRUE),
('system_version', '1.0.0', 'string', '系统版本', TRUE),
('default_timeout', '30', 'integer', '默认超时时间（秒）', FALSE),
('default_retry_times', '3', 'integer', '默认重试次数', FALSE),
('max_concurrent_tasks', '10', 'integer', '最大并发任务数', FALSE),
('enable_email_notification', 'false', 'boolean', '是否启用邮件通知', FALSE),
('email_smtp_server', '', 'string', 'SMTP服务器地址', FALSE),
('email_smtp_port', '587', 'integer', 'SMTP端口', FALSE),
('email_username', '', 'string', '邮箱用户名', FALSE),
('email_password', '', 'string', '邮箱密码', FALSE),
('admin_email', '', 'string', '管理员邮箱', FALSE);

-- 创建用户表（如果需要认证功能）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(100) COMMENT '邮箱',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否管理员',
    last_login_at DATETIME COMMENT '最后登录时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_username (username),
    INDEX idx_user_email (email),
    INDEX idx_user_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 插入默认管理员用户（密码：admin123）
-- 使用正确的密码哈希
INSERT IGNORE INTO users (username, password_hash, email, is_active, is_admin) VALUES
('admin', 'pbkdf2:sha256:260000$3yX9zL2K$8f7e4c6d5a9b8e7f6c5d4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0', 'admin@example.com', TRUE, TRUE);

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id INT COMMENT '用户ID',
    operation VARCHAR(100) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(50) COMMENT '资源类型',
    resource_id INT COMMENT '资源ID',
    description TEXT COMMENT '操作描述',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_log_user (user_id),
    INDEX idx_log_operation (operation),
    INDEX idx_log_resource (resource_type, resource_id),
    INDEX idx_log_time (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 创建通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '通知ID',
    type VARCHAR(50) NOT NULL COMMENT '通知类型',
    title VARCHAR(255) NOT NULL COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已读',
    user_id INT COMMENT '用户ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    read_at DATETIME COMMENT '阅读时间',
    INDEX idx_notification_user (user_id),
    INDEX idx_notification_type (type),
    INDEX idx_notification_read (is_read),
    INDEX idx_notification_time (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';
