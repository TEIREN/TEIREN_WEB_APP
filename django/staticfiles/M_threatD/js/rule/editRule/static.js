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

function ruleEditAction(event){
    var data = $('#edit_form').serialize()
    var modal = $('#edit .card-body.shadow')[0]
    $(modal).prepend(`
        <div id="temp" style="background-color: #ffffffb8; height: -webkit-fill-available; width: -webkit-fill-available; display: flex; position: absolute; z-index: 9999; border-radius: 20px; margin: -2% 2% 1% -2%; justify-content: center; align-items: center;">
            <div id="loader" class="spinner-border text-teiren" style="position:absolute; margin:25% 45%; z-index:9999;"></div>
        <div>
    `)
    $.ajax({
        url: '/threat/custom/edit/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(data){
        $('#temp').remove()
        $('#loader').remove()
        alert(data)
        if (data == 'Added Rule Successfully'){
            $('.modal').modal('hide')
            window.location.reload()
        }
    }).fail(function(data){
        $('#temp').remove()
        $('#loader').remove()
        alert('Failed To Add Rule. Please Try Again')
    })
}

function addProperty(logType){
    var count = $('#properties').find('.prop').length + 1
    $.ajax({
        url:'/threat/custom/add/static_slot/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        type: 'post',
        data:{
            count: count,
            log_type: logType
        }
    }).done(function(data){
        $('#properties').append(data)
        $('#properties').find('#property'+count).hide().slideDown('normal')
    })
}

function deleteProperty(e){
    var prop = $(e).parent().parent().parent()
    prop.slideUp('normal')
    setTimeout(function(){
        prop.remove()
        resetStaticNumbers('.prop')
    }, 300)
}

function resetStaticNumbers(e){
    for (var i=0; i<$(e).length; i++){
        $(e)[i].id = $(e)[i].id.slice(0,-1)+(i+1)
        var input = $($(e)[i]).find('input')
        input.each(function(){
            if ($(this)[0].list){
                var datalist = $(this)[0].list.id.slice(0,-1)+(i+1)
                $(this)[0].list.id = datalist
                $($(this)[0]).attr('list', datalist)
            }
            $($(this)[0]).attr('name', $(this)[0].name.slice(0,-1)+(i+1))
            $($(this)[0]).attr('placeholder', $(this)[0].placeholder.slice(0,-1)+(i+1))
            var span = $($(this)[0]).parent().children('span')[0]
            span.innerText = span.innerText.slice(0,-1)+(i+1)
        })
    }
}

function newPropertyKey(e){
    var num = e.name.slice(-1)
    if(e.value == 'New Property'){
        $("#properties").find("#property"+num).append(
            `
            <div id="property_key_custom_${num}" class="col-4">
                <span>New Property</span>
                <input type="text-area" class="form-control form-control-user" name="property_custom_${num}" placeholder="New Property">
            </div>
            `
        )
    } else {
        if($("#property_key_custom_"+num).length > 0){
            $("#property_key_custom_"+num).remove()
        }
    }
}