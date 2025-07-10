-- 网址监控系统数据库初始化脚本
-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 使用指定数据库
USE website_monitor;

-- 创建用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL UNIQUE,
  `email` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_admin` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_username` (`username`),
  KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建网站分组表
CREATE TABLE IF NOT EXISTS website_groups (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分组ID',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '分组名称',
    description TEXT COMMENT '分组描述',
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认分组',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_group_name (name),
    INDEX idx_group_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='网站分组表';

-- 创建网站信息表
CREATE TABLE IF NOT EXISTS websites (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '网站ID',
    name VARCHAR(255) NOT NULL COMMENT '网站名称',
    url TEXT NOT NULL COMMENT '网站URL',
    domain VARCHAR(255) NOT NULL COMMENT '中文域名',
    original_url TEXT NOT NULL COMMENT '原始网址',
    normalized_url TEXT COMMENT '标准化网址',
    description TEXT COMMENT '网站描述',
    group_id INT COMMENT '所属分组ID',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_website_name (name),
    INDEX idx_website_domain (domain),
    INDEX idx_website_domain_active (domain, is_active),
    INDEX idx_website_group (group_id),
    INDEX idx_website_active (is_active),
    INDEX idx_website_created (created_at),
    FOREIGN KEY (group_id) REFERENCES website_groups(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='网站信息表';

-- 创建检测任务表
CREATE TABLE IF NOT EXISTS detection_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    interval_hours INT NOT NULL DEFAULT 6 COMMENT '检测间隔(小时)',
    max_concurrent INT DEFAULT 10 COMMENT '最大并发数',
    timeout_seconds INT DEFAULT 30 COMMENT '超时时间(秒)',
    retry_times INT DEFAULT 3 COMMENT '重试次数',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    is_running BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否运行中',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_run_at DATETIME COMMENT '上次运行时间',
    next_run_at DATETIME COMMENT '下次运行时间',
    total_runs INT DEFAULT 0 COMMENT '总运行次数',
    success_runs INT DEFAULT 0 COMMENT '成功运行次数',
    failed_runs INT DEFAULT 0 COMMENT '失败运行次数',
    INDEX idx_task_name (name),
    INDEX idx_task_active (is_active),
    INDEX idx_task_running (is_running),
    INDEX idx_task_next_run (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检测任务表';

-- 创建检测记录表
CREATE TABLE IF NOT EXISTS detection_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    website_id INT NOT NULL COMMENT '网站ID',
    task_id INT COMMENT '任务ID',
    status VARCHAR(20) NOT NULL COMMENT '检测状态',
    final_url TEXT COMMENT '最终访问URL',
    response_time FLOAT COMMENT '响应时间(秒)',
    http_status_code INT COMMENT 'HTTP状态码',
    error_message TEXT COMMENT '错误信息',
    failure_reason VARCHAR(50) COMMENT '失败原因类型',
    ssl_info JSON COMMENT 'SSL证书信息',
    redirect_chain JSON COMMENT '重定向链',
    page_title TEXT COMMENT '网页标题',
    page_content_length INT COMMENT '页面内容长度',
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    detection_duration FLOAT COMMENT '检测耗时(秒)',
    INDEX idx_detection_website (website_id),
    INDEX idx_detection_task (task_id),
    INDEX idx_detection_status (status),
    INDEX idx_detection_time (detected_at),
    INDEX idx_detection_website_time (website_id, detected_at),
    INDEX idx_detection_status_time (status, detected_at),
    INDEX idx_detection_task_time (task_id, detected_at),
    INDEX idx_detection_failure_reason (failure_reason),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检测记录表';

-- 创建任务网站关联表
CREATE TABLE IF NOT EXISTS task_websites (
    task_id INT NOT NULL COMMENT '任务ID',
    website_id INT NOT NULL COMMENT '网站ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (task_id, website_id),
    INDEX idx_task_websites_task (task_id),
    INDEX idx_task_websites_website (website_id),
    FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务网站关联表';
