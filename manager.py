from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models  # 只需要导入模型类就可完成数据库迁移


# manager是程序启动的入口，只关心启动相关的内容，不关心集体该如何创建视图函数的逻辑

# 通过传入配置参数初始化app对象
from info.models import User

app = create_app('development')

# 使用Flask-Script迁移扩展
manager = Manager(app)

# 迁移类关联数据库存储对象和当前应用
Migrate(app, db)  # 注意顺序!!!!
manager.add_command('db', MigrateCommand)  # 迁移命令添加到manager中方便从终端完成迁移


@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def createsuperuser(name, password):
    """命令行创建超级用户"""
    if not all([name, password]):
        print("参数不足")
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    # 提交到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print("添加超级用户成功")


if __name__ == '__main__':
    manager.run()
