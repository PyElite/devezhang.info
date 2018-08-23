from info import redis_store
from . import index_blu


@index_blu.route('/')
def index():
    # 向redis中保存一个值:作为一个redis操作测试
    redis_store.set('name', 'itcast')

    return 'hello'
