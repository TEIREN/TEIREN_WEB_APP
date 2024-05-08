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

$('#search').on('keypress', function(e){
    if(e.which === 13){
        e.preventDefault();
    }
})

/// Search_Filter
function searchFilter(){
    $('#asset_table').hide()
    $.ajax({
        url: '/compliance/assets/search/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: $('#search').serialize(),
        type: 'post'
    }).done(function(response){
        if(response.trim().startsWith('<head')){
            location.reload()
            return 0
        }
        $('#dataTable').DataTable().destroy()
        $('#asset_table').html(response)
        $('#dataTable').DataTable({
            info: true,
            searching: false,
            lengthChange: false
        })
        $('#asset_table').show()
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