/**
 * Created by 东方鹗 on 15-7-15.
 */
$(function () {
    $('[data-toggle="tooltip"]').tooltip({
        html : true
    })
    $('[data-toggle="popover"]').popover({
        animation  : true,
        html       : true
    })
    $('#nav-tab a').click(function (e) {
        e.preventDefault()
        $(this).tab('show')
    })
    $('[data-toggle="offcanvas"]').click(function(){
        $('.sidebar').fadeToggle(1000)
    })

    /***
    $('ul.nav > li').click(function (e) {
        e.preventDefault();
        $('ul.nav > li').removeClass('active');
        $(this).addClass('active');
    })
     ***/
    $('input[type=file]').on('change', function(){
        var file = this.files[0];
        //获取文件当前到url
        var url = null;
        if (window.createObjectURL!=undefined) { // basic
            url = window.createObjectURL(file) ;
        } else if (window.URL!=undefined) { // mozilla(firefox)
            url = window.URL.createObjectURL(file) ;
        } else if (window.webkitURL!=undefined) { // webkit or chrome
            // url = window.webkitURL.createObjectURL(file) ;
        }else{
            return;
        }
        if (url) {
            $('#picture').attr("src", url)
        }
    })
})