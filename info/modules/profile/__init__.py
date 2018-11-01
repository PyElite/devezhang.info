# 注册个人中心相关逻辑的蓝图

from flask import Blueprint

# 创建蓝图对象
profile_blu = Blueprint('profile', __name__, url_prefix='/user')

from . import views