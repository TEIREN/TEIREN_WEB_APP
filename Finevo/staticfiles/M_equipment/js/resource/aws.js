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

function secretkey() {
    var x = document.getElementById("secret_key");
    if (x.type === "password") {
        x.type = "text";
    }
    else {
        x.type = "password";
    }
};

$('#form-check').on('click', function () {
    var data = $('#account_form').serialize()
    $.ajax({
        url: 'check/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function (data) {
        document.getElementById("form-check").className = data.class;
        document.getElementById("form-check").value = data.value;
        if (data.modal) {
            document.getElementById("insert").type = 'button';
            $('#insert').on('click', function (event) {
                document.getElementById("modal_access_key").value = data.modal.access_key;
                document.getElementById("modal_secret_key").value = data.modal.secret_key;
                document.getElementById("modal_region_name").value = data.modal.region_name;
                document.getElementById("modal_group_name").value = data.modal.group_name;
                $('#modal').modal('show');
            });
        };
    })
})

$('#insert_accept').on('click', function (event) {
    var data = $('#insertform').serialize();
    $.ajax({
        url: 'insert/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: data,
        type: 'post'
    }).done(function (response) {
        if(!response.startsWith('Success')){
            $('#message').addClass('text-danger')
            $("#message").html(response);
        } else {
            $('#message').addClass('text-teiren')
            $("#message").html(response);
            $('.modal-body').remove();
            $("#modal_title").text(`AWS ${logType} Integrated Successfully`);
            $('#insert_check').remove();
            $('#insert_complete').attr('type', 'button');
        }
    }).fail(function () {
        $('#message').addClass('text-danger')
        $("#message").text('Failed To Integrate. Please Check Your Inputs');
    })
});

$('#insert_complete').on('click', function (event) {
    $('#modal').modal('hide');
    window.location = document.referrer;
});