function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $(".news_edit").submit(function (e) {
        e.preventDefault()
        // 新闻编辑提交

        // ajaxSubmmit模拟ajax的方式完成表单提交，会自动拼接带name的input标签组成字典
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
            url: "/admin/news_edit_detail",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 返回上一页，刷新数据
                    location.href = document.referrer;
                } else {
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