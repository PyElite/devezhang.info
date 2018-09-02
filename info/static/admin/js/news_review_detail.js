function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $(".news_review").submit(function (e) {
        e.preventDefault()

        // 新闻审核提交
        // serializeArray(自动获取带name的input拼成字典)与ajax一起完成模拟表单提交的操作

        var params = {};
        // 获取到所有的参数
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value;
        });
        // 取到参数以便判断
        var action = params["action"];
        var news_id = params["news_id"];
        var reason = params["reason"];
        if (action == "reject" && !reason) {
            alert('请输入拒绝原因');
            return;
        }
        // 整理参数
        params = {
            "action": action,
            "news_id": news_id,
            "reason": reason
        }
        $.ajax({
            url: "/admin/news_review_detail",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 请求成功，则返回上一页，刷新数据
                    location.href = document.referrer;
                }else {
                    // 请求失败，则弹出失败信息
                    alert(resp.errmsg);
                }
            }
        })

    })
})

// 点击取消，返回上一页
function cancel() {
    history.go(-1)
}