from backend.app import create_app
from backend.models import init_db, create_default_settings

print("正在初始化数据库...")

# 创建一个Flask应用实例以获取应用上下文
app = create_app()

with app.app_context():
    print("创建所有数据库表...")
    init_db(app)
    print("数据库表创建完成。")
    
    print("创建默认系统设置...")
    create_default_settings()
    print("默认设置创建完成。")

print("数据库初始化成功！")