from flask import render_template, g, redirect, request, jsonify

from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@profile_blu.route("/info")
@user_login_data
def user_info():
    """用户个人信息"""
    user = g.user
    if not user:
        # 用户没有登录则冲定向到首页
        return redirect("/")

    data = {
        "user": user.to_dict()
    }

    return render_template("news/user.html", data=data)


@profile_blu.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    """基本资料"""
    # 不同的请求函数做不同的事情
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user})
    else:
        # 代表修改数据
        # 1.取参
        params = request.json
        nick_name = params.get("nick_name")
        signature = params.get("signature")
        gender = params.get("gender")
        # 2.校参
        if not all([nick_name, signature, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        if gender not in ("WOMAN", "MAN"):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 3.修改数据
        user = g.user  # 当前用户,直接赋值即是修改，会自动提交
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender
        return jsonify(errno=RET.OK, errmsg="OK")

