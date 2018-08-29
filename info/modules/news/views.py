from flask import render_template, session, current_app, g, abort, jsonify, request

from info import constants, db
from info.models import User, News, Comment
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    """新闻详情"""

    # 1.查询用户是否登录
    user = g.user
    # user_id = session.get('user_id', None)
    # user = None  # 避免用户未登录时查询模型失败
    # if user_id:
    #     # 已经登录则尝试查询用户模型
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    # 2.右侧新闻排行
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    # 遍历分页查询结果转成字典存入新的列表
    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())
    # 3.点击查询新闻数据
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        abort(400)  # 没有此新闻，请求无效
    # 更新新闻点击数
    news.clicks += 1
    # 4.收藏状态
    is_collected = False
    if g.user:  # 如果已登录则判断是否已收藏
        if news in g.user.collection_news:
            is_collected = True

    # 5.查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    # 遍历评论数据，转成属性字典存入新的列表
    comment_dict_li = []
    for comment in comments:
        comment_dict_li = comment.to_dict()
        comment_dict_li.append(comment)

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "news": news,
        "is_collected": is_collected,
        "comments":comment_dict_li
    }

    return render_template('news/detail.html', data=data)


@news_blu.route("/news_collect", methods=["POST"])
@user_login_data
def collect_news():
    """新闻收藏"""
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.取参
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    # 2.校参
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)  # 尝试转换成整数用于查询
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 3.查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
    # 4.取消收藏
    if action == "cancel_collect":
        user.collection_news.remove(news)  # 字典用pop
    # 5.收藏
    else:
        if news not in user.collection_news:
            user.collection_news.append(news)  # append学了？
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route("/news_comment", methods=["POST"])
@user_login_data
def comment_news():
    """新闻评论"""
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.取参
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    # 2.校参
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)  # 尝试转换成整数用于查询
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 3.查询参数
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
    # 4.初始化评论模型，并给字段赋值
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id

    # 5.添加到数据库
        # 需要自己commit，因为下方需要返回数据
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
    # 6.响应
    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())







