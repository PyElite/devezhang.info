var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = true;   // 是否正在向后台获取数据


$(function () {
    // 界面加载完成后加载新闻数据
    updateNewsData()

    // 首页分类切换
    $('.menu li').click(function () {
        // 点击之后获取当前点击cid
        var clickCid = $(this).attr('data-cid')
        // 遍历所有列表，清除active
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        // 给当前点击对象添加active类
        $(this).addClass('active')

        // 如果点击cid不等于当前cid,则设置当前cid为点击cid,实现切换cid分类
        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            // 切换分类后请求状态改为false
            data_querying = false
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // TODO 判断页数，去更新新闻数据
            if (!data_querying){  // 加载完成时已设置此状态为false，则可以通过
                // 如果正在请求数据，则将其标记为True
                data_querying = true;
                if (cur_page<total_page){
                    // 当前页加1，再调用页面更新
                    cur_page+=1;
                    // 如果正请求的当前页数没到达总页数，则请求数据
                    updateNewsData();
                }else {
                    // 否则已经是最大页数，则请求状态标记为false
                    data_querying = false;
                }
            }
        }
    })
})

function updateNewsData() {
    // TODO 更新新闻数据
    var params = {
        'page': cur_page,
        'cid': currentCid,
        'per_page': 10
    }
    $.get('/news_list', params, function (resp) {
        // 加载完成，设置请求状态为false
        data_querying = false
        if (resp.errno == '0'){
            // 代表请求成功
            total_page = resp.data.total_page

            if(cur_page == 1){
                // 判断如果当前是第一页，则清空原数据；
                $('.list_con').html("");
            }
            // 显示数据
            for (var i=0;i<resp.data.news_dict_li.length;i++){
                var news = resp.data.news_dict_li[i];
                var content = '<li>'
                content += '<a href="/news/'+news.id+'" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="/news/'+news.id+'" class="news_title fl">' + news.title + '</a>'
                content += '<a href="/news/'+news.id+'" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                // html添加内容数据，append从后面贴
                $(".list_con").append(content)
            }
        }else{
            // 代表请求失败
            alert(resp.errmsg)
        }
    })
}
