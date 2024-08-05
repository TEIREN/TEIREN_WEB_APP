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

$('#verify_modal').on('show.bs.modal', function(event) {
    input = $(this).find('input')
    input.each(function(){
        if(this.name === 'user_name'){
            this.value = $(event.relatedTarget).data('name')
        }
        else{
            this.value = ''
        }
    })
});

$('#delete_modal').on('show.bs.modal', function(event) {
    input = $(this).find('input')
    input.each(function(){
        if(this.name === 'user_name'){
            this.value = $(event.relatedTarget).data('name')
        }
        else{
            this.value = ''
        }
    })
});


function verifyAccount(){
    var data = $('#verify_account').serialize()
    $.ajax({
        url:'verify/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type:'post'
    }).done(function(response){
        if(response.startsWith('[Verification Fail]')){
            alert(response)
        }
        else if (response.startsWith('\n<meta')){
            location.reload()
        } 
        else if (response === ''){
            alert('[Verification Fail] Unknown information. Please check your information.')
        }
        else {
            $('#edit_detail').html('')
            $('#edit_detail').append(response)
            $('#verify_modal').modal('hide')
            $('#edit_modal').modal('show')
        }
    })
}

function editAccount(){
    var data = $('#edit_account').serialize()
    $.ajax({
        url:'update/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type:'post'
    }).done(function(response){
        if (response.startsWith('\n<meta')){
            location.reload()
        } 
        alert(response)
        if (response.startsWith('Successfully')){
            location.reload()
        }
    })
}

function deleteAccount(){
    var data = $('#delete_account').serialize()
    $.ajax({
        url:'delete/',
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type:'post'
    }).done(function(response){
        if (response == 'reload'){
            alert('Deleted Account Successfully')
            location.reload()
            return 0
        }
        if (response.startsWith('Delete')){
            alert(response)
            location.reload()
        } else {
            alert(response)
        }
    })
}