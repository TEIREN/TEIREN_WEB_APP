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


$("#dataTable").DataTable({
    ordering: false,
    // 표시 건수기능 숨기기
    lengthChange: false,
    // 검색 기능 숨기기
    searching: false,
    info: false
})

$('#search').on('keypress', function(e){
    if (e.which === 13){
        event.preventDefault();
    }
})

function versionModify(){
    $('#com_table').fadeOut('fast')
    $.ajax({
        url:`/compliance/lists/${compliance_type}/modify/`,
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: $('#search').serialize(),
        type: 'post'
    }).done(function(response){
        $("#dataTable").DataTable().destroy();
        $('#com_table').html(response)
        $("#dataTable").DataTable({
            ordering: false,
            // 표시 건수기능 숨기기
            lengthChange: false,
            // 검색 기능 숨기기
            searching: false,
            info: false
        })
        $('#com_table').fadeIn('fast')
    })
    
}

function scoreChange(e){
    var value = e.value
    var article = $(e.parentNode).find('.com_article').val()
    var product = $('#com_product').val()
    var version = $('#com_version').val()
    $.ajax({
        url:`/compliance/lists/${compliance_type}/modify/`,
        headers:{
            'X-CSRFToken': getCookie()
        },
        data:{
            version: version,
            product: product,
            article : article,
            value :value
        },
        type: 'post'
    }).done(function(response){
        if (response === 'Fail'){
            alert('Comply Modification Fail')
            versionModify()
        }
    })
}
