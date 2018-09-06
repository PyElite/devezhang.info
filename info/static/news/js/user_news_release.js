function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {

    $(".release_form").submit(function (e) {
        e.preventDefault()

        // 发布完毕之后需要选中我的发布新闻
        // ajaxSubmit使用ajax的方式去模拟点击提交按钮的操作
        // ajaxSubmit自动收集带name的input标签，将name和value拼接之后作为ajax提交的数据提交到后台
        $(this).ajaxSubmit({

            beforeSubmit: function (request) {
                // 在提交之前，对参数进行处理
                for(var i=0; i<request.length; i++) {
                    var item = request[i]
                    if (item["name"] == "content") {
                        // 前段框架，将value值渲染成富文本返回
                        item["value"] = tinyMCE.activeEditor.getContent()
                    }
                }
            },

            url: "/user/news_release",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边单菜单
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else {
                    alert(resp.errmsg)
                }
            }
        })

        // // 选中索引为6的左边单菜单
        // window.parent.fnChangeMenu(6)
        // // 滚动到顶部
        // window.parent.scrollTo(0, 0)
    })
})