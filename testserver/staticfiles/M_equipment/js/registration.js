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

$('form').on('submit', function(e){
    e.preventDefault();
});

$('.search-input').on('keyup', function(e){
    if (e.which !== 13){
        filterSearch();
    }
})

function filterSearch(){
    var data = $('#search').serializeArray()
    let key = data[0].value
    let value = data[1].value
    if (value === ''){
        $('.registration').fadeIn()
        $('.registration a').fadeIn()
        return 0
    }
    if (key === 'All'){
        $('.registration').each(function(){
            if (!new RegExp(value.toUpperCase(), 'i').test($(this).text().toUpperCase())){
                $(this).fadeOut('fast')
            } else {
                $(this).fadeIn()                
                if (!new RegExp(value.toUpperCase(), 'i').test($(this).find('.regi-header h6').text().toUpperCase())){
                    $(this).find('a').each(function(){
                        $(this).find('span').each(function(){
                            if (!new RegExp(value.toUpperCase(), 'i').test($(this).text().toUpperCase())){
                                $(this).parent().fadeOut('fast')
                            } else {
                                $(this).parent().fadeIn()
                                return false
                            }
                        })
                    })
                }
            }
        })
    } else {
        $('.registration').each(function(){
            if (!new RegExp(key.toUpperCase(), 'i').test($(this).find('.regi-header h6').text().toUpperCase())){
                $(this).fadeOut('fast')
            } else {
                $(this).fadeIn()
                $(this).find('a').each(function(){
                    $(this).find('span').each(function(){
                        if (!new RegExp(value.toUpperCase(), 'i').test($(this).text().toUpperCase())){
                            $(this).parent().fadeOut('fast')
                        } else {
                            $(this).parent().fadeIn()
                            return false
                        }
                    })
                })
            }
        })
    }
}

$('#integration_side').addClass('active');