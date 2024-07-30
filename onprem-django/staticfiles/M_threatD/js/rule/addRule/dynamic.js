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


function addNewDynamicRule(){
    $('#count').val($('#dynamic_rules .rule').length)
    var data = $('#new_rules').serialize()
    var modal = $('#rule-modal .card-body.shadow')[0]
    $(modal).prepend(`
        <div id="temp" style="background-color: #ffffffb8; height: -webkit-fill-available; width: -webkit-fill-available; display: flex; position: absolute; z-index: 9999; border-radius: 20px; margin: -2% 2% 1% -2%; justify-content: center; align-items: center;">
            <div id="loader" class="spinner-border text-teiren" style="position:absolute; margin:25% 45%; z-index:9999;"></div>
        <div>
    `)
    $.ajax({
        url: '/threat/custom/add/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function(response){
        $('#temp').remove()
        $('#loader').remove()
        alert(response)
        if(response == 'Added Rule Successfully'){
            window.location.reload()
        }
    })
}

function addDynamicSlot(){
    var count = $('#new_rules').find('.rule').length
    $('#rule_'+count).remove()
    $.ajax({
        url:'/threat/custom/add/dynamic_slot/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        type: 'post',
        data:{
            count: count,
            log_type: logType
        }
    }).done(function(data){
        $('#dynamic_rules').append(data)
        $('#rule_'+count).slideDown('normal')
    })
}

function deleteDynamicSlot(e){
    var num = $(e).parent().parent().parent()[0].id.slice(-1)
    $('#rule_'+num).slideUp('normal')
    setTimeout(function(){
        $('#rule_'+num).remove()
        resetRuleNumbers(num)
    }, 300)
}

function addDynamicProperty(flow_num){
    var prop_num = $('#rule_'+flow_num).find('.prop').length + 1
    $.ajax({
        url:'/threat/custom/add/dynamic_property_slot/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data:{
            log_type: logType,
            flow_num: flow_num,
            prop_num: prop_num
        },
        type: 'post'
    }).done(function(response){
        $('#flow'+flow_num+'_'+prop_num).remove()
        $('#rule_'+flow_num).find('.properties').append(response)
        $('#flow'+flow_num+'_'+prop_num).hide().slideDown('normal')
    })
}

function deleteDynamicProperty(e){
    var num = $(e).parent().parent().attr('id').slice(-3)
    var flow_num = num[0]
    var prop_num = Number(num[2])
    $('#flow'+flow_num+'_'+prop_num).slideUp('normal')
    setTimeout(function(){
        $('#flow'+flow_num+'_'+prop_num).remove()
        resetPropertyNumbers(flow_num)
    }, 500)
}

function dynamicFlow(){
    $.ajax({
        url: '/threat/custom/add/flow_check/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: {
            log_type: logType,
            rules: $('#dynamic_rules input').serialize(),
            rule_count: $('#dynamic_rules .rule').length,
            flow_count: 1
        },
        type: 'post'
    }).done(function(response){
        if(response.startsWith('error')){
            var error = response.slice(6)
            alert(error)
        }
        else{
            $('.slotbtn').fadeOut()
            $('.dynamic_content').slideUp('normal')
            $('#dynamic_flow').fadeIn()
            $('#flow_content').append(response)
        }
    }) 
}

function dynamicRule(){
    $('#dynamic_flow').fadeOut()
    $('.slotbtn').fadeIn()
    $('.dynamic_content').slideDown('normal')
    $('#flow_content').children().remove()
}

function addFlow(){
    var count = $('.flow').length+1
    $.ajax({
        url:'/threat/custom/add/flow_slot/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: {
            log_type: logType,
            rules: $('#dynamic_rules input').serialize(),
            rule_count: $('#dynamic_rules .rule').length,
            flow_count: count
        },
        type: 'post'
    }).done(function(response){
        $('#flow_content').append(response)
        $('#flow_'+count).hide().slideDown('normal')
    })
}

function deleteFlow(e){
    var num = $(e).parent().parent().parent()[0].id.slice(-1)
    $('#flow_'+num).slideUp('normal')
    setTimeout(function(){
        $('#flow_'+num).remove()
        resetFlowNumbers(num)
    }, 500)
}

function newPropertyKey(e){
    var num = e.name.slice(-3)
    if(e.value == 'New Property'){
        $(".properties").find("#flow"+num).append(
            `
            <div id="flow_key_custom_${num}" class="col-6 mt-1">
                <span>New Property</span>
                <input type="text-area" class="form-control form-control-user" name="flow_custom_${num}" placeholder="New Property">
            </div>
            `
        )
    } else {
        if($("#flow_key_custom_"+num).length > 0){
            $("#flow_key_custom_"+num).remove()
        }
    }
}

function resetPropertyNumbers(num){
    var prop = $('#rule_'+num).find('.prop')
    prop.each(function(i){
        this.id = `${this.id.slice(0,-3)}${num}_${i+1}`
        var input = $(this).find('input')
        input.each(function(){
            this.name = `${this.name.slice(0,-3)}${num}_${i+1}`
            if (this.list){
                this.list.id = `${this.list.id.slice(0,-3)}${num}_${i+1}`
                $(this).attr('list', `${$(this).attr('list').slice(0,-3)}${num}_${i+1}`)
            }
        })
    })
}

function resetRuleNumbers(num){
    $('.rule').each(function(i){
        if (i == 0){ return true }
        this.id = `${this.id.slice(0,-1)}${i}`
        $(this).find('.row h5').text(`Flow Detection ${i}`)
        var input = $(this).find('input').slice(0,2)
        input.each(function(){
            this.name = `${this.name.slice(0,-3)}${i}_1`
        })
        $(this).find('button.mr-auto').each(function(){
            if($(this).text() == '+'){
                $(this).attr('onclick', `addDynamicProperty(${i})`)
            }
        })
        resetPropertyNumbers(i)
    })
}

function resetFlowNumbers(num){
    $('.flow').each(function(i){
        this.id = `${this.id.slice(0,-1)}${i+1}`
        $(this).find('.row h6').text(`Dynamic Detection ${i+1}`)
        var select = $(this).find('select')
        select.each(function(){
            if (this.name.includes('logical')){
                this.name = `${this.name.slice(0,-1)}${i}`
            }
            else{ this.name = `${this.name.slice(0,-1)}${i+1}` }
        })
        var input = $(this).find('input')
        input.each(function(){
            this.name = `${this.name.slice(0,-1)}${i+1}`
            if (this.list){
                this.list.id = `${this.list.id.slice(0,-1)}${i+1}`
                $(this).attr('list', `${$(this).attr('list').slice(0,-1)}${i+1}`)
            }
        })
    })
}