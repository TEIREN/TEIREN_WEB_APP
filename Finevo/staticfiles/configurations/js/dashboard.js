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

// Page Init -----------------------------------------------------------------------------------------------------------------------------
$(function () {
    $('.grid-stack').append(
        `<div id="temp" class="d-flex justify-content-center align-items-center" style="width:100%; height:50vh;">
            <button class="h1 btn btn-teiren" onclick="toggleLayoutSidebar()">Select Layout</button>
        </div>`
    )

    $('#defaultCheckbox').on('click', function(){
        this.classList.toggle('active')
        $('.savebtn').prop('disabled', false)
    })

    $('#newLayout-modal').on('hidden.bs.modal', function () {
        $('#newLayoutName').val('')
    })
})

// Sidebar -----------------------------------------------------------------------------------------------------------------------------
function toggleItemSidebar() {
    var sidebar = document.getElementById('itemSidebar');
    sidebar.classList.toggle('open')
}

function toggleLayoutSidebar() {
    var sidebar = document.getElementById('layoutSidebar');
    sidebar.classList.toggle('open')
}

function closeSidebar(e) {
    var sidebar = e.parentNode.parentNode
    sidebar.classList.toggle('open')
}

// Grid and Widget/Item ----------------------------------------------------------------------------------------------------------------
var grid = 0
$.ajax({
    url: "/grid/items/",
    headers: {
        'X-CSRFToken': getCookie()
    },
    type: 'post'
}).done(function (data) {
    grid = GridStack.init({
        float: false,
        resizable: { handles: 'all' },
        acceptWidgets: true,
        minRow: 8,
        fitToContent: false,
        cellHeight: 10,
        margin: 1,
        removable: '#delete-box',
    });
    grid.on('removed', function (event, items) {
        for (i in items) {
            if (items[i].content) {
                var item = $(items[i].content)[0].id
                $(`#${item}btn`).show()
            }
        }
    });
    
    grid.on('change', function (event, items) {
        $('.savebtn').prop('disabled', false);
    })
    
    grid.on('added', function (event, items) {
        for (i in items) {
            if (items[i].el.id) {
                var sidebar = document.getElementById('itemSidebar');
                addItem(items[i].el.id.slice(0, -3))
                grid.removeWidget(items[i].el)
                sidebar.classList.remove('open');
            }
        }
        $('.savebtn').prop('disabled', false);
    })
    result = data.items
    for (i in result) {
        var itemName = result[i]
        var item = $('<div>', { id: `${itemName}btn`, class: "newWidget grid-stack-item" },).text(`Add ${itemName}`)
        $('#itemList').append(item)
    }
    GridStack.setupDragIn('#itemList .newWidget', { appendTo: 'body', helper: 'clone' });
})

function addItem(type) {
    $.ajax({
        url: `/grid/items/${type}/`,
        headers: {
            'X-CSRFToken': getCookie()
        },
        type: 'post'
    }).done(function (data) {
        grid.addWidget(data)
        var scripts = $(data.content).filter('script:not([src])');
        if (scripts.length >= 1) {
            $.each(scripts, function (idx, script) {
                var jsvar = JSON.parse(script.text)
                for (var key in jsvar) {
                    window[key] = jsvar[key]
                }
            })
        }
        var scriptSrc = $(data.content).filter('script').attr('src');
        if (scriptSrc) {
            $.getScript(scriptSrc)
        }
        $(`#${type}btn`).hide()
        if (type == 'recentDetection') {
            $.ajax({
                url: `/grid/items/graphitem/`,
                headers: {
                    'X-CSRFToken': getCookie()
                },
                type: 'post'
            }).done(function (data) {
                grid.addWidget(data)
            })
        }
    })
}

// Layout -----------------------------------------------------------------------------------------------------------------------------
$.ajax({
    url: "/grid/layouts/",
    headers: {
        'X-CSRFToken': getCookie()
    },
    type: 'post'
}).done(function (data) {
    for (i in data) {
        layout = $('<div>', { class: "layoutList row" })
        layout.append($('<span>', { class: "d-flex align-items-center" }).text(data[i]))
        layout.append($('<button>', { class: "btn btn-md btn-danger ml-auto delbox", onclick: "deleteLayout(this)" }).text('Delete'))
        layout.append($('<button>', { class: "btn btn-md btn-teiren ml-2", onclick: "loadLayout(this)" }).text('Load Layout'))
        $('#layoutList').append(layout)
    }
})

function editLayout() {
    var delboxes = $('.layoutList .delbox')
    if (delboxes) {
        delboxes.each(function () {
            var $this = $(this);
            if ($this.css('opacity') === '0') {
                $this.css({
                    'opacity': '1',
                    'pointer-events': 'auto'
                })
            }
            else {
                $this.css({
                    'opacity': '0',
                    'pointer-events': 'none'
                })
            }
        })
    }
}

function newLayout() {
    var name = $('#newLayoutName').val()
    var serializedData = grid.save()
    for (i in serializedData) {
        let el = serializedData[i]
        el.id = $(el.content)[0].id
    }
    $.ajax({
        url: '/grid/new/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: {
            name: name,
            data: JSON.stringify(serializedData)
        },
        type: 'post'
    }).done(function (data) {
        if (data !== 'Saved Successfully') {
            alert(data)
        }
        else {
            layout = $('<div>', { class: "layoutList row" })
            layout.append($('<span>', { class: "d-flex align-items-center" }).text(name))
            layout.append($('<button>', { class: "btn btn-sm btn-danger ml-auto delbox", onclick: "deleteLayout(this)" }).text('Delete'))
            layout.append($('<button>', { class: "btn btn-sm btn-teiren ml-2", onclick: "loadLayout(this)" }).text('Load Layout'))
            layout.hide()
            $('#layoutList').append(layout)
            layout.slideDown('normal')
            var delboxes = $('.layoutList .delbox')
            if (delboxes) {
                delboxes.each(function () {
                    var $this = $(this);
                    $this.css({
                        'opacity': '0'
                    })
                })
            }
        }
    })
}

function saveLayout() {
    var name = $('#layoutName').text()
    var isDefault = $('#defaultCheckbox').hasClass('active')? 1:0
    if (name) {
        var serializedData = grid.save()
        for (i in serializedData) {
            let el = serializedData[i]
            el.id = $(el.content)[0].id
        }
        $.ajax({
            url: '/grid/save/',
            headers: {
                'X-CSRFToken': getCookie()
            },
            data: {
                name: name,
                data: JSON.stringify(serializedData),
                isDefault: isDefault
            },
            type: 'post'
        }).done(function (data) {
            alert(data)
        })
    }
    else {
        alert('Layout Name Is Missing')
    }
}
function loadLayout(e) {
    document.getElementById('layoutSidebar').classList.remove('open');
    var name = $(e).parent().children().filter('span')[0].innerText
    $('#temp').remove()
    grid.removeAll()
    $('body').append(
        `<div id="loader" class="d-flex justify-content-center align-items-center" style="width:100vw; height:100vh; background-color:rgba(156, 154, 154, 0.1); position:absolute; top:0">
            <div class="spinner-border-lg text-teiren"></div>
        </div>`
    )
    $('.grid-stack').append(
        `<div id="temp" style="margin:80vh 46vw"></div>`
    )
    $('#layoutName').text(name).show()
    $('#layoutbtns').fadeIn()
    $('#defaultCheckbox').removeClass('active')
    $.ajax({
        url: '/grid/load/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: {
            name: name
        },
        type: 'post'
    }).done(function (data) {
        var data = JSON.parse(data)
        $('#loader').fadeOut()
        setTimeout(() => {
            $('#temp').remove()
            $('#loader').remove()
        }, 1000);
        grid.removeAll()
        grid.load(data)
        for (i in data) {
            $(`#${data[i].id}btn`).hide()
            if (data[i].id === 'graphitem') {
                continue
            }
            var scripts = $(data[i].content).filter('script:not([src])');
            if (scripts.length >= 1) {
                $.each(scripts, function (idx, script) {
                    var jsvar = JSON.parse(script.text)
                    for (var key in jsvar) {
                        window[key] = jsvar[key]
                    }
                })
            }
            var scriptSrc = $(data[i].content).filter('script').attr('src')
            if (scriptSrc) {
                $.getScript(scriptSrc)
            }
        }
        $('.savebtn').prop('disabled', true);
    }).fail(function (data) {
        grid.removeAll()
    })
}

function deleteLayout(e) {
    var layout = $(e).parent()
    var name = layout.children().filter('span')[0].innerText
    $.ajax({
        url: '/grid/delete/',
        headers: {
            'X-CSRFToken': getCookie()
        },
        data: {
            name: name
        },
        type: 'post'
    }).done(function (data) {
        alert(data)
        if (data !== 'Not Saved Layout') {
            layout.slideUp('normal', function () { $(this).remove() })
        }
    })
}

function resetLayout(){
    grid.removeAll()
}

// Delete Box -----------------------------------------------------------------------------------------------------------------------------
var checkExist = setInterval(function () {
    if ($('.ui-draggable-dragging').length) {
        $('#delete-box').show()
    }
    else {
        $('#delete-box').hide()
    }
}, 100);