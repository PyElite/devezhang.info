# 公用工具

from flask import g, session, current_app
import functools

from info.models import User


def user_login_data(func):
    # functools.warps(f)作用：解决一个视图名字对应多个url;
    # 因为在同一个文件内都用这个装饰器会导致包裹的视图名字都是wrapper
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id', None)
        user = None
        if user_id:
            # 已经登录则尝试查询用户模型
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)
    return wrapper

