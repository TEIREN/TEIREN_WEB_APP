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

function threat(e) {
    var data = $(e).serialize()
    $.ajax({
        url: "/threat/neo4j/",
        headers:{
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: "post"
    }).done(function(res) {
        $("#gdb_dashboard").html(res)
        $('#threat_form').append($(e).find('input[type=hidden]').clone())
        $('#threat_form').append('<button class="btn btn-block btn-sm btn-teiren mb-2">Details</button>')
    })
}
var e = $('.gdb_threat').clone()[0]
threat(e)