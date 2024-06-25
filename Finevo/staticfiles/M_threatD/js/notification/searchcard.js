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

//체크박스 전체선택
function selectAll(selectAll, type) {
    $('input.'+type).each(function(){
        if ($(this).val() == 'regex'){
            this.checked = false
            $(`#${type}_regex`).slideUp('fast')
            $(`#${type}_regex input`).val('')
            return 1
        }
        this.checked = selectAll.checked
    })
}

//체크박스 전체선택 해제
function selectcheck(e, type){
    if(e.checked == false){
        $('input[name='+type+'_all]')[0].checked = e.checked
        $(`#${type}_regex`).slideUp('fast')
        $(`#${type}_regex input`).val('')
    }
    else if($(e).val()=='regex'){
        $('input.'+type).each(function(){
            if(this == e){
                return 1
            }
            this.checked = false
        })
        $(e).parent().parent().parent().parent().find('.search-dropdown-menu').hide()
        $(`#${type}_regex`).slideDown('fast')
        $(`#${type}_regex`).focus()
    }
    else{
        var count = 0
        $(`#${type}_regex`).slideUp('fast')
        $(`#${type}_regex input`).val('')
        $('input.'+type).each(function(){
            if($(this).val()== 'regex'){
                this.checked = false
            }
            if(this.checked == true){
                if(($(this).val()== 'regex')){
                    return 1
                }
                count += 1 
            }
        })
        if( count ==  $('input.'+type).length - 1 ){
            $('input[name='+type+'_all]')[0].checked = true
        }
    }
}
/// 체크박스 자동 표시/숨김
$('.searchbox-input').on('focus', function(){
    $(this).parent().find('.search-dropdown-menu').slideDown('fast')
})

$('.searchbox-input').on('blur', function(){
    var dropdown = $(this).parent().find('.search-dropdown-menu')
    var this_var = this
    setTimeout(function() {
        if (!$('.dropdown-item:hover').length){
            if (!$(':checkbox:focus').length){
                dropdown.slideUp('fast');
            }
        }else{
            this_var.focus()
        }
    }, 10);
})
$(':checkbox').on('blur', function(e) {
    var dropdown = $(this).parent().parent().parent().parent().find('.search-dropdown-menu')
    var this_var = this
    setTimeout(function() {
        if (!$('.dropdown-item:hover').length){
            if (!$(':checkbox:focus').length){
                dropdown.slideUp('fast');
            }
        }else{
            this_var.focus()
        }
    }, 10);
});

$('.searchbox-input').on('input', function() {
    var input = $(this).val();

    // Iterate over each checkbox
    $(this).parent().find('.search-dropdown-menu li input[type="checkbox"]').each(function() {
        var checkboxValue = $(this);
        // If the checkbox value doesn't contain the input string, hide it
        if (!new RegExp(input, 'i').test(checkboxValue.val())) {
            $(this).parent().parent().hide();
        } else {
            $(this).parent().parent().show();
        }
    });
});


/// Search_Filter
function searchFilter(page, order=null){
    console.log($('#search').serializeArray())
    if (page == 'reset') {
        var checkbox = $('#search input[type="checkbox"]')
        checkbox.each(function () {
            this.checked = false
        })
        $('.calandar-input').val('')
        $('.search-input')[0].value = ''
        $('.regexbox').slideUp('fast')
        $('.regexbox input').val('')
        page = 1
    }

    if (order){
        $("input[name='order_key']").val(order[0])
        $("input[name='order_value']").val(order[1])
    }

    if ($("input[name='order_key']").val() === ''){
        order = []
    } else {
        order = [$("input[name='order_key']").val(), $("input[name='order_value']").val()]
    }

    var filter = $('#search').serializeArray()
    $.ajax({
        url:'/threat/notifications/filter/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data:{
            filter:JSON.stringify(filter),
            order: order,
            page: page
        },
        traditional:true,
        type:'post'
    }).done(function(response){
        $('#data').html(response)
    })
    return 0
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