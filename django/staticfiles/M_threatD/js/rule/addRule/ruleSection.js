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

function addSection(logType, ruleClass){
    $.ajax({
        url: `/threat/custom/add/${ruleClass}/`,
        headers:{
            'X-CSRFToken': getCookie()
        },
        type: 'post',
        data:{
            log_type: logType,
        }
    }).done(function(data){
        $('#new_rules').append(data)
        $('#rule_0').fadeIn('normal')
        $('#addbtns').slideUp()
    })
    if (ruleClass == 'dynamic'){
        $('#addNewRuleSetbtn').fadeOut('normal')
    }
}

function deleteSection(e){
    $('#rule_'+e).slideUp('normal')
    setTimeout(function(){
        $('#rule_'+e).remove()
    },500)
    if (e == 0){
        $('#addbtns').slideDown()
        $('#addNewRuleSetbtn').fadeIn('normal')
    }
}