from flask import render_template, session, current_app, g, abort, jsonify, request

from info import constants, db
from info.models import User, News, Comment, CommentLike
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    """新闻详情"""

    # 1.查询用户是否登录
    user = g.user
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
    if user:
        # 判断用户是否收藏当前新闻，如果收藏：
        # collection_news 后面可以不用加all，因为sqlalchemy会在使用的时候去自动加载
        if news in user.collection_news:
            is_collected = True

    # 4.1.关注作者
    is_followed = False
    # if 当前新闻有作者，并且 当前登录用户已关注过这个用户
    if news.user and user:
        # if user 是否关注过 news.user
        if news.user in user.followed:
            is_followed = True

    # 5.查询当前新闻评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    # 在加载详情时便判断用户是否登录，如登录则显示其赞了哪些评论
    comment_like_ids = []
    if user:
        try:
            # 1.列表生成式获取当前新闻的所有评论id
            comment_ids = [comment.id for comment in comments]
            if len(comment_ids) > 0:
                # 2.如果当前新闻有评论，查询当前新闻的所有评论的点赞记录
                comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids), CommentLike.user_id==user.id)
                # 3.取出所有点赞记录的id
                comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    # 遍历评论数据，转成属性字典存入新的列表
    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()  # 转成字典
        # 默认没有被点赞
        comment_dict["is_like"] = False
        # 判断当前遍历的评论是否被该用户点赞
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True

        comment_dict_li.append(comment_dict)

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,  # 点击排行榜用
        "news": news.to_dict(),  # to_dict(）渲染模板不用转成字典，jsonify需要转成属性字典
        "is_collected": is_collected,
        "comments": comment_dict_li,
        "is_followed": is_followed
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
        # 尝试转换成整数用于查询，防止通过postman提交；前段的验证不可靠，后端还需验证
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 3.查询新闻,判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
    # 4.存在此新闻，则取消收藏或收藏
    if action == "cancel_collect":
        if news in user.collection_news:  # 如果在列表内再取消
            user.collection_news.remove(news)  # 字典用pop
    # 5.收藏
    else:
        if news not in user.collection_news:
            user.collection_news.append(news)  # append是列表的操作方法
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


@news_blu.route("/comment_like", methods=["POST"])
@user_login_data
def comment_like():
    """评论点赞"""
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.取参
    # news_id = request.json.get("news_id")  # 可以不传news_id,只要判断评论是否存在即可
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")
    # 2.校参
    if not all([action, comment_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.查询参数
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")
    # 4.评论存在：点赞或取消点赞
    # 查询三方关系表是否存在这条赞
    comment_like_model = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
    if action == "add":
        # 点赞
        if not comment_like_model:
            # 实例第三章关系表
            comment_like_model = CommentLike()
            comment_like_model.comment_id = comment_id
            comment_like_model.user_id = g.user.id
            # 添加进数据库
            db.session.add(comment_like_model)
            # 评论表增加点赞条数
            comment.like_count += 1
    else:
        # 取消点赞，查询结果中
        # comment_like_model = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            # 点赞总数-1
            comment.like_count -= 1
    # 统一提交数据, 也可不写，因为已开启请求结束之后自动commit
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    # 响应数据
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    """关注/取消关注用户"""
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    user_id = request.json.get("user_id")
    action = request.json.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到关注的用户信息
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")

    # 根据不同操作做不同逻辑
    if action == "follow":
        # 添加不能关注自己的逻辑
        if user.id == user_id:
            return jsonify(errno=RET.DATAERR, errmsg="您不能关注自己")
        # 关注目标用户
        if target_user not in user.followed:
            target_user.followers.append(g.user)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")

    else:
        if target_user in user.followed:
            target_user.followers.remove(g.user)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前用户未关注")

    # 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存错误")

    return jsonify(errno=RET.OK, errmsg="操作成功")
