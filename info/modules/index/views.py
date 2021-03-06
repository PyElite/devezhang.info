from flask import render_template, current_app, session, request, jsonify, g
from sqlalchemy import or_

from info import constants
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blu


@index_blu.route('/all_news_list')
def news_list():
    """
    获取指定分类的新闻列表
    1. 获取参数
    2. 校验参数
    3. 查询数据
    4. 返回数据
    """

    # 取参:分类id
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)
    # 校参
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 1.查询所有文章并按创建时间进行排序
    try:
        # *filters相当于对filters列表拆包
        paginate = News.query.filter(News.status == 0).order_by(News.create_time.desc()).paginate(page, per_page, False)
        # 获取查询出来的数据
        items = paginate.items
        # 获取总页数
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

    # jsonify发送数据不能是model对象，须转成属性字典
    news_dict_li = []
    for news in items:
        news_dict_li.append(news.to_basic_dict())
    data = {
        'total_page': total_page,
        'current_page': current_page,
        'news_dict_li': news_dict_li,
        'cid': cid
    }

    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@index_blu.route('/archives_news_list')
@user_login_data
def archives_news_list():
    """
    获取指定分类的新闻列表
    1. 获取参数
    2. 校验参数
    3. 查询数据
    4. 返回数据
    """
    # 查询用户
    user = g.user

    # 取参:分类id
    cid = request.args.get('cid', '4')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)
    # 校参
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 1.查询档案分类列表并按创建时间进行排序
    try:
        # *filters相当于对filters列表拆包
        paginate = News.query.filter(News.category_id == cid, News.status == 0).order_by(News.create_time).paginate(page, per_page, False)
        # 获取查询出来的数据
        items = paginate.items
        # 获取总页数
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

    # jsonify发送数据不能是model对象，须转成属性字典
    news_dict_li = []
    for news in items:
        news_dict_li.append(news.to_basic_dict())
    data = {
        'total_page': total_page,
        'current_page': current_page,
        'news_dict_li': news_dict_li,
        "user": user.to_dict() if user else None,
    }

    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@index_blu.route('/')
@user_login_data
def index():
    """主页新闻列表"""

    # 1.查询用户是否登录
    user = g.user

    # 2.右侧新闻排行
    news_li = []
    try:
        # 新闻的审核状态：0通过，1审核中，-1未通过
        news_li = News.query.filter(News.status == 0).order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    # 遍历分页查询结果转成字典存入新的列表
    news_dict_li = []
    for news in news_li:
        news_dict_li.append(news.to_basic_dict())

    # 3.上方新闻分类
    # categories = Category.query.all()
    # ××只查询分类名字为Home/Archives/About
    filters = [Category.name == "Home",
               Category.name == "Archives",
               Category.name == "Project",
               Category.name == "About"
               ]
    categories = []
    try:
        categories = Category.query.filter(or_(*filters)).all()
    except Exception as e:
        current_app.logger.error(e)
    # 空列表保存分类数据
    categories_dicts = []
    # 查询所有，遍历后分别将属性转成字典存入新列表
    for category in categories:
        categories_dicts.append(category.to_dict())

    data = {
        # 如果user有值，则用user.to_dict()，否则为None
        # to_dict()获取user的属性,因为ajax使用json传输数据，不能携带对象
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        'categories': categories_dicts
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/archives')
@user_login_data
def archives():
    """文章档案目录"""
    user = g.user
    # 1.查询排除Home/Archives/About的所有分类，并拼接数据为字典
    filters_archives = [Category.name != "Home",
                        Category.name != "Archives",
                        Category.name != "Project",
                        Category.name != "About"
                       ]
    categories_archives = []
    try:
        categories_archives = Category.query.filter(*filters_archives).all()
    except Exception as e:
        current_app.logger.error(e)
    # 空列表保存分类数据
    categories_archives_li = []
    # 查询所有，遍历后分别将属性转成字典存入新列表
    for category in categories_archives:
        categories_archives_li.append(category.to_dict())

    # 2.查询右侧点击排行数据
    news_li = []
    try:
        # 新闻的审核状态：0通过，1审核中，-1未通过
        news_li = News.query.filter(News.status == 0).order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    # 遍历分页查询结果转成字典存入新的列表
    news_dict_li = []
    for news in news_li:
        news_dict_li.append(news.to_basic_dict())

    # 3.上方新闻分类
    # categories = Category.query.all()
    # ××只查询分类名字为Home/Archives/About
    filters = [Category.name == "Home",
               Category.name == "Archives",
               Category.name == "Project",
               Category.name == "About"
               ]
    categories = []
    try:
        categories = Category.query.filter(or_(*filters)).all()
    except Exception as e:
        current_app.logger.error(e)
    # 空列表保存分类数据
    categories_li = []
    # 查询所有，遍历后分别将属性转成字典存入新列表
    for category in categories:
        categories_li.append(category.to_dict())

    # 4.渲染archives.html页面，并将数据返回
    data = {
        # 如果user有值，则用user.to_dict()，否则为None
        # to_dict()获取user的属性,因为ajax使用json传输数据，不能携带对象
        "user": user.to_dict() if user else None,
        'categories': categories_li,
        "categories_archives": categories_archives,
        "news_dict_li": news_dict_li
    }
    return render_template('news/archives.html', data=data)


# 浏览器默认都请求网站标签的图标，添加此路由对应的视图
@index_blu.route('/favicon.ico')
def favicon():
    # 此处取不到app,可用应用上下文current_app
    # 其send_static_file方法是系统访问静态文件的方法
    return current_app.send_static_file('admin/images/favicon.ico')
