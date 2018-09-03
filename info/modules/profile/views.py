from flask import render_template, g, redirect, request, jsonify, current_app, abort

from info import constants, db
from info.models import Category, News, User
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@profile_blu.route("/info")
@user_login_data
def user_info():
    """用户个人信息"""
    user = g.user
    if not user:
        # 用户没有登录则冲定向到首页
        return redirect("/")

    data = {
        "user": user.to_dict()
    }

    return render_template("news/user.html", data=data)


@profile_blu.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    """基本资料"""
    # 不同的请求函数做不同的事情
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user})
    else:
        # 代表修改数据
        # 1.取参
        params = request.json
        nick_name = params.get("nick_name")
        signature = params.get("signature")
        gender = params.get("gender")
        # 2.校参
        if not all([nick_name, signature, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        if gender not in ("WOMAN", "MAN"):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 3.修改数据
        user = g.user  # 当前用户,直接赋值即是修改，会自动提交
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender
        return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    """用户个人中心基本资料修改"""
    user = g.user
    # 不同的请求函数做不同的事情
    if request.method == "GET":
        return render_template("news/user_pic_info.html", data={"user_info": user.to_dict()})
    else:
        # 代表修改头像
        # 1.取参，获取上传的文件
        try:
            avatar_file = request.files.get("avatar").read()  # 提交时name等于avatar
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="读取文件出错")

        # 2.读取成功则上传到七牛云
        try:
            url = storage(avatar_file)  # 返回的是文件的key，即文件的范文路径
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="上传图片错误")
        # 3.将头像信息更新到当前用户的模型中
        user.avatar_url = url  # 设置用户模型相关数据,将会自动提交

        return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + url})


@profile_blu.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    """用户个人中心密码修改"""
    if request.method == "GET":  # 加载输入密码页面不需要获取用户对象
        return render_template("news/user_pass_info.html")
    else:
        # POST 提交，执行密码修改
        # 1.获取参数2个：old_password/new_password,参数格式json
        params = request.json
        old_password = params.get("old_password")
        new_password = params.get("new_password2")
        # 2.校参,前端判断是否相等，后端判断是否全部有值
        if not all([old_password, new_password]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 3.获取当前用户信息
        user = g.user
        # 原密码的hash值是否争取
        if not user.check_password(old_password):
            return jsonify(errno=RET.PWDERR, errmsg="原密码错误")
        # 更新用户数据,将会自动提交
        user.password = new_password
        return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_blu.route("/collection")
@user_login_data
def user_collection():
    """用户个人中心新闻收藏页面"""
    # 前段通过get请求从url中传递当前页数，后端负责从当前用户的收藏中获取分页对象；
    # 将当前页目，总页目分页数据以及所有收藏新闻传递前段进行分页显示
    # 1.取参：当前页数
    p = request.args.get("p", 1)  # 没有值则默认第一页
    # 2，校参:凡是整数类型的值都要转成int，一保证严谨，二下方有可能通过整数获取对象
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1  # 如果传递的值不正确，默认显示第一页
    # 3，查询当前对象的收藏数据
    user = g.user
    collections = []
    current_page = 1
    total_page = 1
    try:  # 尝试查询用户所有收藏新闻的分页数据；
        # paginate3个参数(显示第page页,每页per_page个,error_out=False不抛出404错误)
        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取分页数据
        collections = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 收藏列表转成字典存入新的列表
    collection_dict_li = []
    for collection in collections:
        # 根据需要转成审核所需要的字典数据
        collection_dict_li.append(collection.to_basic_dict())
    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": collection_dict_li
    }
    return render_template("news/user_collection.html", data=data)


@profile_blu.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    """用户个人中心新闻发布"""
    if request.method == "GET":  # 加载页面不需要获取用户对象
        # 新闻分类查询
        categorys = []
        try:
            categorys = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_li = []
        for category in categorys:
            category_dict_li.append(category.to_dict())
        # 移除“最新”分类
        category_dict_li.pop(0)

        return render_template("news/user_news_release.html", data={"categories": category_dict_li})
    else:
        # POST 提交，执行发布新闻操作
        # 1.获取要提交的数据
        title = request.form.get("title")  # 标题
        source = "个人发布"
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")
        # 2.校参 判断数据是否有值
        if not all([title, source, digest, content, index_image, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
        try:
            category_id = int(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 3.尝试读取图片(将来显示到主页),上传到七牛
        try:
            index_image_data = index_image.read()  # 上面已经验证有值，不用分开try
            key = storage(index_image_data)  # 将主页图片数据上传给七牛返回生成图片url
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")

        # 3. 初始化新闻模型，并设置相关数据
        news = News()
        news.title = title
        news.digest = digest  # 摘要
        news.source = source  # 新闻来源
        news.content = content
        # 加url前缀,index_image_url表示首页图片地址
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.user_id = g.user.id
        # 代表待审核状态
        news.status = 1

        # 4. 保存到数据库，不自己提交也没事，会自动提交
        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
        # 5. 返回结果
        return jsonify(errno=RET.OK, errmsg="发布成功，等待审核")


@profile_blu.route("/news_list")
@user_login_data
def user_news_list():
    """用户发布的新闻列表"""
    # 取参：请求页码
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 查询用户新闻并获取分页数据
    user = g.user
    news_li = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取当前页数据，返回的是一个列表
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 将用户的新闻分页数据转成字典存入新的列表
    news_dict_li = []
    for news in news_li:
        # 根据页面审核状态的需求，用to_review_dict()
        news_dict_li.append(news.to_review_dict())
    data = {
        "news_list": news_dict_li,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_news_list.html", data=data)


@profile_blu.route("/user_follow")
@user_login_data
def user_follow():
    """个人中心用户关注的用户列表"""

    user = g.user
    # 取参：请求页码
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 查询用户新闻并获取分页数据
    followers = []
    current_page = 1
    total_page = 1

    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据，返回的是一个列表
        followers = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 将用户的新闻分页数据转成字典存入新的列表
    followers_li = []
    for follower in followers:
        # 根据页面审核状态的需求，用to_review_dict()
        followers_li.append(follower.to_dict())
    data = {
        "followers": followers_li,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_follow.html", data=data)























