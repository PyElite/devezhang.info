import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, jsonify, session, redirect, url_for, g

from info.models import User
from info.modules.admin import admin_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


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
        # 3.验证查询此管理用户是否存在
        try:
            user = User.query.filter(User.mobile == username, User.is_admin == True).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template("admin/login.html", errmsg="数据查询失败")
        if not user:
            return render_template("admin/login.html", errmsg="用户名或密码错误")
        # 4.验证密码是否正确
        if not user.check_password(password):
            return render_template("admin/login.html", errmsg="用户名或密码错误")
        # 5.登陆成功则保存登录状态
        session["user_id"] = user.id
        session["nick_name"] = user.nick_name
        session["mobile"] = user.mobile
        session["is_admin"] = True

        # 6.返回成功界面：主页
        return redirect(url_for("admin.index"))  # admin是蓝图的别名


@admin_blu.route("user_count")
def user_count():
    """用户统计页面"""
    # 1.查询总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 2.查询月新增人数
    now = time.localtime()  # 获取本地时间
    mon_count = 0
    try:
        mon_begin = "%d-%02d-01" % (now.tm_year, now.tm_mon)
        mon_begin_date = datetime.strptime(mon_begin, "%Y-%m-%d")
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 3.查询日新增人数
    day_count = 0
    try:
        day_begin = "%d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.strptime(day_begin, "%Y-%m-%d")
        day_count = User.query.filter(User.is_admin == False, User.create_time >= day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)


    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
    }
    return render_template("admin/user_count.html", data=data)
