import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, jsonify, session, redirect, url_for, g

from info import constants
from info.models import User, News
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
    #   2.1获取本地目前时间
    now = time.localtime()
    mon_count = 0
    try:
        mon_begin_date = datetime.strptime("%d-%02d-01" %
                                           (now.tm_year, now.tm_mon), "%Y-%m-%d")
        mon_count = User.query.filter(User.is_admin == False,
                                      User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 3.查询日新增人数
    day_count = 0
    try:
        day_begin_date = datetime.strptime("%d-%02d-%02d" %
                                           (now.tm_year, now.tm_mon, now.tm_mday), "%Y-%m-%d")
        day_count = User.query.filter(User.is_admin == False,
                                      User.create_time >= day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 4.折线图数据；  strptime将时间字符串按照一定的格式转成时间对象；
    #   4.1获取当天凌晨时间。下取：2018:09:02:00:00:00
    today_date = datetime.strptime("%d-%02d-%02d" %
                                   (now.tm_year, now.tm_mon, now.tm_mday), "%Y-%m-%d")
    #   4.2定义空数据用于保存图标需要的信息
    active_time = []
    active_count = []

    #   4.3添加数据，再反转
    for i in range(0, 31):  # timedelta对象代表事件对象之间的时间差
        # 获得开始时间和结束时间
        begin_date = today_date - timedelta(days=i)
        end_date = today_date - timedelta(days=(i-1))

        # 获得今天活跃的用户量
        count = User.query.filter(User.is_admin == False,
                                  User.last_login >= begin_date,
                                  User.last_login <= end_date).count()
        # 将需要的数据存入列表
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))  # strftime时间对象转成字符串
    # 反转展示
    active_count.reverse()
    active_time.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }
    return render_template("admin/user_count.html", data=data)


@admin_blu.route("/user_list")
def user_list():
    """用户列表展示"""
    # 1.用户列表需要分页，取参：页码
    page = request.args.get("page", 1)
    # 2.校参：int
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    # 3.查询用户并按最后登录时间排序后分页
    users = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin == False).\
                                    order_by(User.last_login.desc()).\
                                    paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 4.将数据转成字典列表
    users_list = []
    for user in users:
        users_list.append(user.to_admin_dict())

    data = {
        "users": users_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/user_list.html", data=data)


@admin_blu.route("news_review")
def news_review_list():
    """新闻待审核列表"""
    # 1.列表需要分页，取参：页码，搜索关键字
    page = request.args.get("page", 1)
    keywords = request.args.get("keywords", "")  # 默认为空，html添加name="keywords"
    # 2.校参：int
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    # 3.查询未审核的新闻并按创建时间排序后分页
    news = []
    current_page = 1
    total_page = 1
    try:
        filters = [News.status != 0]
        if keywords:
            # 关键的检索功能实现:标题包含关键字
            filters.append(News.title.contains(keywords))
        # 分页查询
        paginate = News.query.filter(*filters).\
                                    order_by(News.create_time.desc()).\
                                    paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        news = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 4.将数据转成字典列表
    news_list = []
    for new in news:
        news_list.append(new.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_review.html", data=data)










