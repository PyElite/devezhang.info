from flask import render_template, request, current_app, jsonify, session, redirect, url_for, g

from info.models import User
from info.modules.admin import admin_blu
from info.utils.common import user_login_data


@admin_blu.route("/index")
@user_login_data
def index():
    """管理员主页"""
    # 1.获取用户登录状态
    user = g.user
    return render_template("admin/index.html", user=user.to_dict() if user else None)


@admin_blu.route("/login", methods=["GET", "POST"])
def login():
    """管理员登录界面"""
    if request.method == "GET":
        # 1.判断是否有管理员账户登录，如果有则直接跳转后台主页
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for("admin.index"))
        # 否则跳转至登录
        return render_template("admin/login.html")
    else:
        # 1.登录取参：username/password,方式表单form
        username = request.form.get("username")
        password = request.form.get("password")
        # 2.校参：非空
        if not all([username, password]):
            # 返回页面
            return render_template("admin/login.html", errmsg="参数不足")
        # 3.验证查询此用户是否存在
        try:
            user = User.query.filter(User.mobile == username).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template("admin/login.html", errmsg="数据查询失败")
        if not user:
            return render_template("admin/login.html", errmsg="用户名或密码错误")
        # 4.验证密码是否正确
        if not user.check_password(password):
            return render_template("admin/login.html", errmsg="用户名或密码错误")
        # 5.判断是否是管理员
        if not user.is_admin:
            return render_template("admin/login.html", errmsg="用户权限错误")
        # 6.登陆成功则保存登录状态
        session["user_id"] = user.id
        session["nick_name"] = user.nick_name
        session["mobile"] = user.mobile
        session["is_admin"] = True

        # 7.返回成功界面：主页
        return redirect(url_for("admin.index"))  # admin是蓝图的别名










