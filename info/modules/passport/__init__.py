# 注册逻辑相关逻辑的蓝图

from flask import Blueprint

# 创建蓝图对象
passport_blu = Blueprint('passport', __name__, url_prefix='/passport')

from . import views