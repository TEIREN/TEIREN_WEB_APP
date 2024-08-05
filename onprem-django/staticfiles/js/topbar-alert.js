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

// $(function () {
//     $.ajax({
//         url: '/topbar/alert/',
//         headers: {
//             'X-CSRFToken': getCookie()
//         },
//         type:'post'
//     }).done(function(data){
//         if (data.top_alert){
//             $('#sidebar_alert').removeAttr('hidden')
//             $('#topbar_alert').addClass('text-danger fa-bounce')
//             $('#sidebar_alert').text(data.top_alert.count)
//         }
//         else if (data.no_top_alert){
//             $('#sidebar_alert').attr('hidden', true)
//             $('#topbar_alert').removeClass('text-danger fa-bounce')
//         }
//     })

//     setInterval(function(){
//         $.ajax({
//             url: '/topbar/alert/',
//             headers: {
//                 'X-CSRFToken': getCookie()
//             },
//             type:'post'
//         }).done(function(data){
//             if (data.top_alert){
//                 $('#sidebar_alert').removeAttr('hidden')
//                 $('#topbar_alert').addClass('text-danger fa-bounce')
//                 $('#sidebar_alert').text(data.top_alert.count)
//             }
//             else if (data.no_top_alert){
//                 $('#sidebar_alert').attr('hidden', true)
//                 $('#topbar_alert').removeClass('text-danger fa-bounce')
//             }
//         })
//     }, 5000);
// })