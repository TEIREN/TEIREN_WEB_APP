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

function addRuleModal(logType) {
    $.ajax({
        url: 'add/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: {
            logType: logType
        },
        type: 'post'
    }).done(function(data) {
        $('#rule_body').html(data);
    })
    $('#rule-modal').modal('show');
}

function ruleDetails(e) {
    var url = e.address.value
    var data = $(e).serialize()
    $.ajax({
        url: url,
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(data) {
        $('#detail_body').html(data)
    }).fail(function(){
        $('#detail_body').html('fail')
    })
}

function editRuleModal() {
    var data = $('#edit_modal_form').serialize()
    $('#edit_message').slideUp('normal')
    $.ajax({
        url: 'edit/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(data) {
        $('#edit_body').html(data)
        $('#edit_body').hide().fadeIn()
    })
}

function deleteRuleModal(event) {
    $('#rule_name').html(event.rule_name.value)
    var data = $(event).children('input').clone()
    $('#del_form').html(data)
}

function deleteRuleAction(event) {
    var data = $(event).serialize()
    $.ajax({
        url: '/threat/custom/delete/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(data) {
        if (data == 'Deleted Successfully') {
            $('.modal').modal('hide')
            alert(data)
            window.location.reload()
        } else {
            alert(data)
        }
    }).fail(function() {
        alert('Failed To Delete. Please Try Again')
    })
}

function ruleOnOff(e) {
    var data = $(e.parentNode).serialize()
    $.ajax({
        url: 'on_off/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(on_off) {
        if (on_off === '2'){
            alert('Failed Rule On/Off. Please Try Again')
            return 0
        }
        $(e.parentNode.on_off).val(on_off)
        if (on_off == '1') {
            $(e).val('  On  ')
            $(e).css('background-color', '')
            $(e).css('border-color', '')
        } else {
            $(e).val('  Off  ')
            $(e).css('background-color', '#D3D3D3')
            $(e).css('border-color', '#D3D3D3')
        }
    })
}
$('#threat_side').addClass('active');