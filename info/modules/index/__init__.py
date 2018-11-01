# 创建一个蓝图

from flask import Blueprint

# 创建蓝图对象：index是
index_blu = Blueprint('index', __name__)


from . import views
