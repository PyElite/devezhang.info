from flask import render_template, g, redirect

from info.modules.profile import profile_blu
from info.utils.common import user_login_data


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







