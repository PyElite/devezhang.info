from flask import render_template, session, current_app, g, abort

from info import constants
from info.models import User, News
from info.modules.news import news_blu
from info.utils.common import user_login_data


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

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "news": news,
        "is_collected": is_collected
    }

    return render_template('news/detail.html', data=data)
