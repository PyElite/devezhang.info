# 创建一个蓝图

from flask import Blueprint, request, url_for, session, redirect

# 创建蓝图对象：
admin_blu = Blueprint('admin', __name__)


@admin_blu.before_request
def before_request():

    is_admin = session.get("is_admin", False)
    # 为什么不能加括号？？？？？？
    if not is_admin and not request.url.endswith(url_for("admin.login")):
        # 判断是否有管理员和不是登录页面的请求，如果不是，直接重定向到项目主页
        return redirect('/')


from . import views
