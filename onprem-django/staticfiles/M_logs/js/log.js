function getCookie(name = 'csrftoken') {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$('#help').on('show.bs.modal', function () {
    $.ajax({
        url: '/logs/modal/help/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        type: 'POST'
    }).done(function (data) {
        $('#help-body').html(data)
    })
})
$('#detail-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget);
    var id = button.data('id')
    var logType = button.data('logtype')
    $.ajax({
        url: `/logs/${resourceType}/modal/details/`,
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: {
            id: id,
            logType: logType
        },
        type: 'post'
    }).done(function (data) {
        $('#detail').html(data)
    }).fail(function (data) {
        $('#detail').html('fail')
    })
})
$(function () {
    $('#log_top').addClass('show')
})


/// Search_Filter
function searchFilter(e) {
    // console.log($('#search').serializeArray())
    $('#log_table').fadeOut('normal')
    if (e == 'reset') {
        data = `page=1&logType=${logType}`
        var checkbox = $('#search input[type="checkbox"]')
        checkbox.each(function () {
            this.checked = false
        })
        $('.calandar-input').val('')
        $('.search-input')[0].value = ''
        $('.regexbox').slideUp('fast')
        $('.regexbox input').val('')

    } else {
        data = $('#search').serialize() + `&page=${e}&logType=${logType}`
    }
    $.ajax({
        url: `/logs/${resourceType}/${logType}/filter/`,
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function (response) {
        if (!response.startsWith('<div')){
            window.location.reload()
        }
        $('#searchCollapse').removeClass('show')
        $('#log_table').html(response)
        $('#log_table').fadeIn('fast')
    }).fail(function(e){
        window.location.reload()
    })
}

$('.btn-collapse').on('click', function(){
    var chevron = $($(this).find('.material-symbols-outlined')[0])
    if ($.trim(chevron.text()) == 'expand_more'){
        chevron.text('expand_less')
        $('.searchcard-collapse').fadeIn()
        $('.collapsecard').slideDown()
    } else {
        chevron.text('expand_more')
        $('.collapsecard').slideUp()
        $('.searchcard-collapse').fadeOut()
    }
})

$('.btn-reset').hover(
    function(){
        $('.btn-reset .material-symbols-outlined').toggleClass('fa-spin fa-spin-reverse')
    },
    function(){
        $('.btn-reset .material-symbols-outlined').toggleClass('fa-spin fa-spin-reverse')
    }
)

$('.btn-info').hover(
    function(){
        $('.btn-info .material-symbols-outlined').toggleClass('fa-bounce')
    },
    function(){
        $('.btn-info .material-symbols-outlined').toggleClass('fa-bounce')
    }
)

$('#log_side').addClass('active')