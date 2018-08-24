from flask import request, abort, current_app, make_response

from info import redis_store, constants
from info.utils.captcha.captcha import captcha
# from info.utils.captcha import captcha  ??
from . import passport_blu


@passport_blu.route('/image_code')
def get_image_code():
    # 1、取到请求中携带的参数：args取到url中？后面的参数
    image_code_id = request.args.get('imageCodeId', None)
    # 2、判断参数是否有值
    if not image_code_id:
        return abort(403)
    # 3、生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 4、保存图片验证码文字内容到redis,排错
    try:
        # key,value,max_age
        redis_store.set('ImageCodeId:' + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        # 将异常输出到日志
        current_app.logger.error(e)
        abort(500)

    # 5、返回验证码图片
    response = make_response(image)
    # 设置数据类型，以便浏览器识别什么类型
    response.headers['Content-Type'] = 'image/jpg'

    return response