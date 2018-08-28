# 公用工具
from flask import g, session, current_app
import functools

from info import constants
from info.models import User, News


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


# def news_rank_show(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         news_list = []
#         try:
#             news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
#         except Exception as e:
#             current_app.logger.error(e)
#         # 遍历分页查询结果转成字典存入新的列表
#         news_dict_li = []
#         for news in news_list:
#             news_dict_li.append(news.to_basic_dict())
#         g.news_dict_li = news_dict_li
#     return wrapper
