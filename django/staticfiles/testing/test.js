function getCookie(name) {
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

// $(function () {
//     const csrftoken = getCookie('csrftoken');

//     console.log('js test')
//     $.ajax({
//         url: '/ajax_js/',
//         headers: {
//             'X-CSRFToken': csrftoken
//         },
//         type: 'post',
//         data: {
//             test: 'js ajax test'
//         }
//     }).done(function(data){
//         console.log('js ajax')
//         console.log(data)
//     })
// })


function test(){
    console.log('testtest')
}