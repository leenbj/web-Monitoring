"""
网址监控工具 - 数据模型
定义所有数据库表结构和模型关系
"""

from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, text
from sqlalchemy.dialects.sqlite import JSON

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

# 初始化数据库
db = SQLAlchemy()

# 导出Base供其他模块使用
Base = db.Model


class WebsiteGroup(db.Model):
    """网站分组模型"""
    __tablename__ = 'website_groups'
    
    id = db.Column(db.Integer, primary_key=True, comment='分组ID')
    name = db.Column(db.String(255), nullable=False, unique=True, index=True, comment='分组名称')
    description = db.Column(db.Text, comment='分组描述')
    is_default = db.Column(db.Boolean, default=False, nullable=False, comment='是否默认分组')
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    
    # 关联关系
    websites = db.relationship('Website', backref='group', lazy='dynamic')
    
    def __repr__(self):
        return f'<WebsiteGroup {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'website_count': self.websites.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Website(db.Model):
    """网站信息模型"""
    __tablename__ = 'websites'
    
    id = db.Column(db.Integer, primary_key=True, comment='网站ID')
    name = db.Column(db.String(255), nullable=False, index=True, comment='网站名称')
    url = db.Column(db.Text, nullable=False, comment='网站URL')
    domain = db.Column(db.String(255), nullable=False, index=True, comment='中文域名')
    original_url = db.Column(db.Text, nullable=False, comment='原始网址')
    normalized_url = db.Column(db.Text, comment='标准化网址')
    description = db.Column(db.Text, comment='网站描述')
    group_id = db.Column(db.Integer, db.ForeignKey('website_groups.id'), index=True, comment='所属分组ID')
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True, comment='是否激活')
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    
    # 关联关系
    detection_records = db.relationship('DetectionRecord', backref='website', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        Index('idx_website_domain_active', domain, is_active),
        Index('idx_website_created', created_at),
    )
    
    def __repr__(self):
        return f'<Website {self.domain}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'domain': self.domain,
            'original_url': self.original_url,
            'normalized_url': self.normalized_url,
            'description': self.description,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DetectionRecord(db.Model):
    """检测记录模型"""
    __tablename__ = 'detection_records'
    
    id = db.Column(db.Integer, primary_key=True, comment='记录ID')
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False, index=True, comment='网站ID')
    task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'), index=True, comment='任务ID')
    
    # 检测状态：standard(标准解析), redirect(跳转解析), failed(无法访问)
    status = db.Column(db.String(20), nullable=False, index=True, comment='检测状态')
    
    # 检测结果详情
    final_url = db.Column(db.Text, comment='最终访问URL')
    response_time = db.Column(db.Float, comment='响应时间(秒)')
    http_status_code = db.Column(db.Integer, comment='HTTP状态码')
    error_message = db.Column(db.Text, comment='错误信息')
    failure_reason = db.Column(db.String(50), index=True, comment='失败原因类型')
    ssl_info = db.Column(JSON, comment='SSL证书信息')
    redirect_chain = db.Column(JSON, comment='重定向链')
    
    # 网页信息
    page_title = db.Column(db.Text, comment='网页标题')
    page_content_length = db.Column(db.Integer, comment='页面内容长度')
    
    # 检测元数据
    detected_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, index=True, comment='检测时间')
    retry_count = db.Column(db.Integer, default=0, comment='重试次数')
    detection_duration = db.Column(db.Float, comment='检测耗时(秒)')
    
    # 索引
    __table_args__ = (
        Index('idx_detection_website_time', website_id, detected_at),
        Index('idx_detection_status_time', status, detected_at),
        Index('idx_detection_task_time', task_id, detected_at),
    )
    
    def __repr__(self):
        return f'<DetectionRecord {self.website_id}:{self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'website_id': self.website_id,
            'task_id': self.task_id,
            'status': self.status,
            'final_url': self.final_url,
            'response_time': self.response_time,
            'http_status_code': self.http_status_code,
            'error_message': self.error_message,
            'failure_reason': self.failure_reason,
            'ssl_info': self.ssl_info,
            'redirect_chain': self.redirect_chain,
            'page_title': self.page_title,
            'page_content_length': self.page_content_length,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'retry_count': self.retry_count,
            'detection_duration': self.detection_duration,
        }


class DetectionTask(db.Model):
    """检测任务模型"""
    __tablename__ = 'detection_tasks'
    
    id = db.Column(db.Integer, primary_key=True, comment='任务ID')
    name = db.Column(db.String(255), nullable=False, comment='任务名称')
    description = db.Column(db.Text, comment='任务描述')
    
    # 任务配置
    interval_hours = db.Column(db.Integer, nullable=False, default=6, comment='检测间隔(小时)')
    max_concurrent = db.Column(db.Integer, default=10, comment='最大并发数')
    timeout_seconds = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    retry_times = db.Column(db.Integer, default=3, comment='重试次数')
    
    # 任务状态
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True, comment='是否激活')
    is_running = db.Column(db.Boolean, default=False, nullable=False, comment='是否运行中')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    last_run_at = db.Column(db.DateTime, comment='上次运行时间')
    next_run_at = db.Column(db.DateTime, comment='下次运行时间')
    
    # 统计信息
    total_runs = db.Column(db.Integer, default=0, comment='总运行次数')
    success_runs = db.Column(db.Integer, default=0, comment='成功运行次数')
    failed_runs = db.Column(db.Integer, default=0, comment='失败运行次数')
    
    # 关联关系
    detection_records = db.relationship('DetectionRecord', backref='task', lazy='dynamic')
    websites = db.relationship('Website', secondary='task_websites', backref='tasks')
    
    def __repr__(self):
        return f'<DetectionTask {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'interval_hours': self.interval_hours,
            'max_concurrent': self.max_concurrent,
            'timeout_seconds': self.timeout_seconds,
            'retry_times': self.retry_times,
            'is_active': self.is_active,
            'is_running': self.is_running,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'total_runs': self.total_runs,
            'success_runs': self.success_runs,
            'failed_runs': self.failed_runs,
        }


# 任务-网站关联表
task_websites = db.Table('task_websites',
    db.Column('task_id', db.Integer, db.ForeignKey('detection_tasks.id'), primary_key=True),
    db.Column('website_id', db.Integer, db.ForeignKey('websites.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=get_beijing_time)
)

# 失败网站监控任务-网站关联表
failed_site_monitor_websites = db.Table('failed_site_monitor_websites',
    db.Column('monitor_task_id', db.Integer, db.ForeignKey('failed_site_monitor_tasks.id'), primary_key=True),
    db.Column('website_id', db.Integer, db.ForeignKey('websites.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=get_beijing_time)
)


class SystemSetting(db.Model):
    """系统设置模型"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True, comment='设置ID')
    key = db.Column(db.String(100), nullable=False, unique=True, index=True, comment='设置键')
    value = db.Column(db.Text, comment='设置值')
    description = db.Column(db.Text, comment='设置描述')
    category = db.Column(db.String(50), index=True, comment='设置分类')
    data_type = db.Column(db.String(20), default='string', comment='数据类型')
    is_active = db.Column(db.Boolean, default=True, nullable=False, comment='是否激活')
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'data_type': self.data_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class UploadRecord(db.Model):
    """文件上传记录模型"""
    __tablename__ = 'upload_records'
    
    id = db.Column(db.Integer, primary_key=True, comment='记录ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    original_filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.Text, nullable=False, comment='文件路径')
    file_size = db.Column(db.Integer, comment='文件大小(字节)')
    file_type = db.Column(db.String(50), comment='文件类型')
    
    # 处理状态：pending(待处理), processing(处理中), completed(完成), failed(失败)
    status = db.Column(db.String(20), default='pending', index=True, comment='处理状态')
    error_message = db.Column(db.Text, comment='错误信息')
    
    # 统计信息
    total_rows = db.Column(db.Integer, comment='总行数')
    processed_rows = db.Column(db.Integer, comment='已处理行数')
    success_rows = db.Column(db.Integer, comment='成功行数')
    failed_rows = db.Column(db.Integer, comment='失败行数')
    
    # 时间信息
    uploaded_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, index=True, comment='上传时间')
    processed_at = db.Column(db.DateTime, comment='处理完成时间')
    
    def __repr__(self):
        return f'<UploadRecord {self.original_filename}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status,
            'error_message': self.error_message,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'success_rows': self.success_rows,
            'failed_rows': self.failed_rows,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }


class UserFile(db.Model):
    """用户文件管理模型"""
    __tablename__ = 'user_files'
    
    id = db.Column(db.Integer, primary_key=True, comment='文件ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    original_filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.Text, nullable=False, comment='文件路径')
    file_size = db.Column(db.Integer, comment='文件大小(字节)')
    file_type = db.Column(db.String(50), comment='文件类型')
    
    # 文件来源：upload(用户上传), download(用户下载)
    source_type = db.Column(db.String(20), nullable=False, index=True, comment='文件来源')
    
    # 下载相关信息（仅当source_type为download时）
    original_export_path = db.Column(db.Text, comment='原始导出文件路径')
    download_count = db.Column(db.Integer, default=0, comment='下载次数')
    last_download_at = db.Column(db.DateTime, comment='最后下载时间')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, index=True, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    
    def __repr__(self):
        return f'<UserFile {self.original_filename}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'source_type': self.source_type,
            'download_count': self.download_count,
            'last_download_at': self.last_download_at.isoformat() if self.last_download_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class WebsiteStatusChange(db.Model):
    """网站状态变化记录模型"""
    __tablename__ = 'website_status_changes'
    
    id = db.Column(db.Integer, primary_key=True, comment='变化记录ID')
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False, index=True, comment='网站ID')
    task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'), index=True, comment='任务ID')
    
    # 状态变化信息
    previous_status = db.Column(db.String(20), comment='之前状态')
    current_status = db.Column(db.String(20), nullable=False, index=True, comment='当前状态')
    change_type = db.Column(db.String(20), nullable=False, index=True, comment='变化类型: became_accessible, became_failed, status_changed')
    
    # 检测详情
    previous_detection_id = db.Column(db.Integer, db.ForeignKey('detection_records.id'), comment='上次检测记录ID')
    current_detection_id = db.Column(db.Integer, db.ForeignKey('detection_records.id'), comment='当前检测记录ID')
    
    # 变化时间
    detected_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, index=True, comment='检测到变化的时间')
    
    # 索引
    __table_args__ = (
        Index('idx_status_change_website_time', website_id, detected_at),
        Index('idx_status_change_type_time', change_type, detected_at),
    )
    
    def __repr__(self):
        return f'<WebsiteStatusChange {self.website_id}:{self.previous_status}->{self.current_status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'website_id': self.website_id,
            'website_name': self.website.name if self.website else None,
            'website_url': self.website.url if self.website else None,
            'task_id': self.task_id,
            'previous_status': self.previous_status,
            'current_status': self.current_status,
            'change_type': self.change_type,
            'previous_detection_id': self.previous_detection_id,
            'current_detection_id': self.current_detection_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
        }


class FailedSiteMonitorTask(db.Model):
    """失败网站专项监控任务模型"""
    __tablename__ = 'failed_site_monitor_tasks'
    
    id = db.Column(db.Integer, primary_key=True, comment='任务ID')
    name = db.Column(db.String(255), nullable=False, comment='任务名称')
    description = db.Column(db.Text, comment='任务描述')
    parent_task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'), nullable=False, index=True, comment='父任务ID')
    
    # 任务配置
    interval_hours = db.Column(db.Integer, default=1, nullable=False, comment='检测间隔(小时)')
    max_concurrent = db.Column(db.Integer, default=10, comment='最大并发数')
    timeout_seconds = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    retry_times = db.Column(db.Integer, default=3, comment='重试次数')
    
    # 任务状态
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True, comment='是否激活')
    is_running = db.Column(db.Boolean, default=False, nullable=False, comment='是否运行中')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=get_beijing_time, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, nullable=False, comment='更新时间')
    last_run_at = db.Column(db.DateTime, comment='上次运行时间')
    next_run_at = db.Column(db.DateTime, comment='下次运行时间')
    
    # 监控网站（失败状态的网站）
    monitored_websites = db.relationship('Website', secondary='failed_site_monitor_websites', backref='failed_monitor_tasks')
    
    # 关联到父任务
    parent_task = db.relationship('DetectionTask', backref='failed_monitor_tasks')
    
    def __repr__(self):
        return f'<FailedSiteMonitorTask {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_task_id': self.parent_task_id,
            'parent_task_name': self.parent_task.name if self.parent_task else None,
            'interval_hours': self.interval_hours,
            'max_concurrent': self.max_concurrent,
            'timeout_seconds': self.timeout_seconds,
            'retry_times': self.retry_times,
            'is_active': self.is_active,
            'is_running': self.is_running,
            'monitored_websites_count': len(self.monitored_websites),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
        }


# 用户管理相关模型

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    real_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, user
    status = db.Column(db.String(20), nullable=False, default='active')  # active, inactive, locked
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time)
    
    def set_password(self, password: str):
        """设置密码"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """检查密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'role': self.role,
            'status': self.status,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建默认系统设置
        create_default_settings()


def create_default_settings():
    """创建默认系统设置"""
    default_settings = [
        {
            'key': 'email_smtp_server',
            'value': 'smtp.qq.com',
            'description': 'SMTP服务器地址',
            'category': 'email',
            'data_type': 'string'
        },
        {
            'key': 'email_smtp_port',
            'value': '587',
            'description': 'SMTP端口',
            'category': 'email',
            'data_type': 'integer'
        },
        {
            'key': 'email_use_tls',
            'value': 'true',
            'description': '是否使用TLS',
            'category': 'email',
            'data_type': 'boolean'
        },
        {
            'key': 'detection_default_interval',
            'value': '60',
            'description': '默认检测间隔(分钟)',
            'category': 'detection',
            'data_type': 'integer'
        },
        {
            'key': 'detection_max_concurrent',
            'value': '20',
            'description': '最大并发检测数',
            'category': 'detection',
            'data_type': 'integer'
        },
        {
            'key': 'detection_timeout',
            'value': '30',
            'description': '检测超时时间(秒)',
            'category': 'detection',
            'data_type': 'integer'
        },
    ]
    
    for setting_data in default_settings:
        existing = SystemSetting.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSetting(**setting_data)
            db.session.add(setting)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"创建默认设置失败: {e}") 