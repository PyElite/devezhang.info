function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        e.preventDefault();

        // 修改密码；分析：需要返回数据格式json,因此不能用ajaxSubmit提交；
        // 可以用serializeArrey自动获取带name的表单，其与ajax共同完成ajaxSubmit的功能
        var params = {};
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value;
        });
        // 前端实现两次密码的一致性判断，后端完成旧密码的hash验证
        var new_password1 = params["new_password1"];
        var new_password2 = params["new_password2"];
        if (new_password1 != new_password2){
            alert("两次密码不一致");
            return
        }
        $.ajax({
            url:"/user/pass_info",
            type:"POST",
            contentType:"application/json",
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },
            data:JSON.stringify(params),
            success:function (resp) {
                if (resp.errrno == "0"){
                    // 0表示修改成功
                    alert("修改成功")
                    // 成功后界面刷新
                    window.location.reload()
                }else {
                    // 否则修改失败
                    alert(resp.errmsg)
                }
            }
        })

    })
})