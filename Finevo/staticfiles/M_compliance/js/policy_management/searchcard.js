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

/// Search_Filter
function searchFilter(){
    $.ajax({
        url: '',
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
        $('#evidence_dataTable').DataTable().destroy()
        $('#evidence_dataTable').html(response)
        $('#evidence_dataTable').DataTable({
            info: true,
            searching: false,
            lengthChange: false
        })
    })
}


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
$('#compliance_side').addClass('active');