from flask import render_template, current_app

from info import redis_store
from . import index_blu


@index_blu.route('/')
def index():
    # # 向redis中保存一个值:作为一个redis操作测试
    # redis_store.set('name', 'itcast')
    return render_template('news/index.html')


# 浏览器默认都请求网站标签的图标，添加此路由对应的视图
@index_blu.route('/favicon.ico')
def favicon():
    # 此处取不到app,可用应用上下文current_app
    # 其send_static_file方法是系统访问静态文件的方法
    return current_app.send_static_file('news/favicon.ico')