import random
import re
from datetime import datetime

from flask import abort, current_app, make_response, jsonify, session, request

from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu


@passport_blu.route('/image_code')
def get_image_code():
    """
    1、取到请求参数：args取到url中？后面的参数；一个请求对应一个id
    2、判断参数有值：没有值抛出403异常
    3、生成图片验证码：captcha包的generate_captcha()
    4、保存验证码内容到redis：排错
    5、设置响应类型：image作为响应体，内容类型image/jpg
    6、返回响应：
    """
    # 取参数
    image_code_id = request.args.get('imageCodeId', None)

    # 断有值
    if not image_code_id:
        return abort(403)
    # 生成验证码：name是图片名字，text是图片的内容信息
    name, text, image = captcha.generate_captcha()
    current_app.logger.debug(text)

    try:
        # key,value,max_age；
        # set源码,第三个参数是过期时间，默认是None
        # setex源码，中间的参数是过期时间
        redis_store.set('ImageCodeId:' + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        # 将异常输出到日志
        current_app.logger.error(e)
        abort(500)

    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    1、获取参数：手机号、图片验证码内容、验证码随机编号
    2、校验参数：是否合规则(参数是否有值、手机号是否正确)，是否有值
    3、redis取值:如果以上两个验证通过
    4、进行对比:不一致返回验证码错误
    5、生成验证码:否则即是一致，随机数据内容
    6、发送短信验证码:
    7、保存验证码到redis：以便提交时校验短信
    8、告知发送结果
    """
    # 取参
    params_dict = request.json
    mobile = params_dict.get('mobile')
    image_code = params_dict.get('image_code')
    image_code_id = params_dict.get('image_code_id')
    # 校参
    if not all([mobile, image_code, image_code_id]):
        # 处理成json字符串返回，默认转request的data
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if not re.match('1[135678]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 从redis中取码
    try:
        real_image_code = redis_store.get('ImageCodeId:' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已失效')
    # 对比
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码填写错误')
    # 生成随机码
    sms_code_str = '%06d' % random.randint(0, 999999)

    current_app.logger.debug(sms_code_str)

    # # 云通讯发送验证码:CCP必须加括号
    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 60], '1')
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
    # 储存验证码到redis
    try:
        redis_store.set('SMS:' + mobile, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errrno=RET.DBERR, errmsg='保存数据失败')
    # 返回发送成功
    return jsonify(errno=RET.OK, errmsg='发送成功')


@passport_blu.route('/register', methods=['POST'])
def register():
    """
    1、获取参数
    2、判断有值
    3、取redis验证码
    4、检验验证码
    5、初始化user模型，添加数据到数据库
    6、保存用户状态
    7、返回结果
    """
    # 取参
    params_dict = request.json
    mobile = params_dict.get('mobile')
    # smscode = params_dict.get('smscode')
    password = params_dict.get('password')

    image_code = params_dict.get('image_code')
    image_code_id = params_dict.get('image_code_id')

    # 判断是否手机号用户已经注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="用户名查询错误")
    # 手机号用户已存在
    if user:
        return jsonify(errno=RET.NODATA, errmsg="该用户名已注册")
    # 判断昵称用户是否已经注册
    try:
        user = User.query.filter(User.nick_name == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="用户名查询错误")
    if user:
        return jsonify(errno=RET.NODATA, errmsg="该用户名已注册")

    # 用户名尚未注册,进行校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # if not re.match('1[135678]\\d{9}', mobile):
    if not re.match(r'.{2}.*', mobile, re.U):
        return jsonify(errno=RET.PARAMERR, errmsg='用户名最短2位')

    # 从redis中取码
    try:
        real_image_code = redis_store.get('ImageCodeId:' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已失效')
    # 对比
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码填写错误')

    # 从redis中取码
    # try:
    #     real_sms_code = redis_store.get('SMS:' + mobile)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    # if not real_sms_code:
    #     return jsonify(errno=RET.NODATA, errmsg='短信验证码已失效')
    # # 对比
    # if real_sms_code != smscode:
    #     return jsonify(errno=RET.DATAERR, errmsg='验证码填写错误')

    # 一致，则实例user模型到数据库
    user = User()
    user.mobile = mobile

    # 昵称暂时设为电话
    user.nick_name = mobile
    # 最后登录时间
    user.last_login = datetime.now()
    # 需求：设置password是对其加密，且将结果赋值给password_hash
    # 已在模型类中通过property装饰器实现
    user.password = password
    try:
        # SQLAlchemy会话管理
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    # 在sesison中保存数据表示已经登录，默认登录
    session['user_id'] = user.id
    # 后续会用下面俩
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 返回注册成功
    return jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blu.route('/login', methods=["POST"])
def login():
    # 取参
    # 校验有值
    # 校验手机
    # 取密码
    # 判断不为空，# 校验密码是否一致
    params_dict = request.json
    mobile = params_dict.get('mobile')
    password = params_dict.get('password')

    # 校验有值
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验手机
    if not re.match(r'.{2}.*', mobile, re.U):
        return jsonify(errno=RET.PARAMERR, errmsg="用户名格式错误")
    # 取密码
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断不为空
    if not user:
        try:
            user = User.query.filter(User.nick_name == mobile).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
        if not user:
            return jsonify(errno=RET.NODATA, errmsg="用户名或密码错误")
    # 校验密码是否一致
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或密码错误")

    # 保存用户状态
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 保存用户最后一次的登录时间到数据库中，将自动commit
    user.last_login = datetime.now()
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     db.session.rollback()

    # 响应
    return jsonify(errno=RET.OK, errmsg='登陆成功')


@passport_blu.route('/logout')
def logout():
    """退出登录"""
    # 1.清除普通用户的session
    session.pop('user_id', None)
    session.pop('mobile', None)
    session.pop('nick_name', None)
    # 2.清除管理员的session:如果管理员登录后进入了普通界面，退出时需要清除is_admin
    session.pop("is_admin", None)
    return jsonify(errno=RET.OK, errmsg='退出成功')