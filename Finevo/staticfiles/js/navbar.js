$('.topbar .nav-link').on('click',function(){
    $('.topbar .collapse').removeClass('open')
    $($(this).parent().find('.collapse')[0]).addClass('open')
})

// $('.sidebar .nav-link').on('click', function(){
//     $('.nav-link').removeClass('focus')
//     $('.sidebar .collapse').removeClass('open')
//     $($(this).parent().find('.collapse')[0]).addClass("open")
//     $(this).addClass('focus')
// })

$('.sidebar .nav-link .tippy').on('click', function(){
    $('.nav-link').removeClass('focus')
    $('.sidebar .collapse').removeClass('open')
    $($(this).parent().parent().find('.collapse')[0]).addClass("open")
    $(this).parent().addClass('focus')
})

$('.sidebar .collapse-hide-btn').on('click', function(){
    $('.nav-link').removeClass('focus')
    $('.sidebar .collapse').removeClass('open')
})

$('.sidebar .item-toggle .item-header').on('click',function(){
    var chevron = $($(this).find('.material-symbols-outlined')[0])
    var buttons = $(this).parent().find('a')
    if ($.trim(chevron.text()) == 'expand_more'){
        chevron.text('expand_less')      
        buttons.each(function(){
            $(this).slideDown()
        })
    } else {
        chevron.text('expand_more')
        buttons.each(function(){
            $(this).slideUp()
        })
    }
})

$(document).click(function(event) {
    var target = $(event.target);
    if (!target.closest(".sidebar .collapse").length & !target.closest(".sidebar .tippy").length) {
        $(".sidebar .nav-link").removeClass('focus')
        $(".sidebar .collapse").removeClass('open');
        $(".sidebar .item-toggle a").hide();
        $(".sidebar .item-toggle .item-header .material-symbols-outlined").text('expand_more')
    }
    if (!target.closest(".topbar .collapse").length & !target.closest(".topbar .nav-link").length) {
        $(".topbar .collapse").removeClass('open');
    }
});

$('.sidebar-search').on('keyup', function(e){
    sidebarSearch($(e.target).parent())
})

function sidebarSearch(e){
    var value = $(e[0]).find('input').val()
    $(e[0]).parent().find('.item-toggle').each(function(){
        if (!new RegExp(value.toUpperCase(), 'i').test($(this).text().toUpperCase())){
            $(this).fadeOut('fast')
            $(this).find('.item-header .material-symbols-outlined').text('expand_more')
            $(this).prev().fadeOut('fast')
        } else {
            $(this).fadeIn()
            $(this).prev().fadeIn()
            $(this).find('.item-header .material-symbols-outlined').text('expand_more')
            $(this).find('a').each(function(){
                if(!new RegExp(value.toUpperCase(), 'i').test($(this).text().toUpperCase())){
                    $(this).fadeOut('fast')
                } else {
                    if(value == ''){
                        $(this).find('.item-header .material-symbols-outlined').text('expand_more')
                        $(this).fadeOut()
                    } else {
                        $(this).parent().find('.item-header .material-symbols-outlined').text('expand_less')
                        $(this).fadeIn()
                    }
                }
            })
        }
    })
}