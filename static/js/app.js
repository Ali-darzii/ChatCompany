let currentRecipient = '';
let currentGroup = '';
let chatInput = $('#chat-input');
let chatButton = $('#btn-send');
let clipButton = $('#clip-input');
let userList = $('#user-list');
let messageList = $('#messages');

// function works in order

$(document).ready(function () {
    updateUserList();
    updateGroupList();
    disableInput();
    var socket = new WebSocket(
        'ws://' + window.location.host +
        '/ws?session_key=${sessionKey}')

    // var socket = new WebSocket(
    //     'ws://' + window.location.host +
    //     `/ws?session_key=${sessionKey}`)

    chatInput.keypress(function (e) {
        if (e.keyCode == 13)
            chatButton.click();
    });

    chatButton.click(function () {
        if (chatInput.val().length > 0) {
            sendMessage(currentRecipient, chatInput.val());
            chatInput.val('');
        }
    });
    socket.onmessage = function (e) {
        getMessageById(e.data);
    };
    console.log(socket);
});




function updateUserList() {
    /*
    get api all users that related to each other(one company)
    remove all users for page refresh(duplicate)
    get every username put it in <a> tag in append it to user list
    remove all active class in user list and put active class on selected one
    to chat be open
    */

    $.getJSON('api/v1/user/', function (data) {
        userList.children('.user').remove();
        for (let i = 0; i < data.length; i++) {
            const userItem = `<a class="list-group-item user">${data[i]['username']}</a>`;
            $(userItem).appendTo('#user-list');
        }
        $('.user').click(function () {
            userList.children('.active').removeClass('active');
            let selected = event.target;
            $(selected).addClass('active');
            setCurrentRecipient(selected.text);

        });
    });


}


function updateGroupList()  {
    $.getJSON('api/v1/groups/', function (data) {
        for (let i = 0; i < data.length; i++) {
            const userItem = `<a class="list-group-item group">${data[i]['title']}</a>`;
            $(userItem).appendTo('#user-list');
        }
        $('.group').click(function () {
            userList.children('.active').removeClass('active');
            let selected = event.target;
            $(selected).addClass('active');
            setCurrentRecipient(selected.text);
        });
    })
}

function disableInput() {
    // we wait for client to click the user and enable!
    chatInput.prop('disabled', true);
    chatButton.prop('disabled', true);
    clipButton.prop('disabled', true);

}

function setCurrentRecipient(username) {
    /*
    submit who is recipient to go fetch message data,
    and we use it in drawMessage
    */

    currentRecipient = username;
    console.log(currentRecipient);
    getConversation(currentRecipient);
    enableInput();
}

function getConversation(recipient) {
    /*
    get api to fetch get old messages
    delete all messages for page refresh(duplicate)
    for any messages we send it to drawMessage function

    */
    $.getJSON(`/api/v1/message/?target=${recipient}`, function (data) {
        messageList.children('.message').remove();
        for (let i = data['results'].length - 1; i >= 0; i--) {
            drawMessage(data['results'][i]);
        }
        messageList.animate({scrollTop: messageList.prop('scrollHeight')});
    });

}

function enableInput() {
    //for fetching message we can't send message(for message order)

    chatInput.prop('disabled', false);
    chatButton.prop('disabled', false);
    clipButton.prop('disabled', false);
    chatInput.focus();
}

function getMessageById(message) {
    /*

    important: we can send the message directly, but we can't
    specify the sender user and recipient
    code: from server will give us the message id and api give
    us {id,body(message),user(sender),recipient(receiver)}
    and after that we chck the user is in the chat box with the
    recipient, and we call the drawMessage function and same for
    recipient and if statement is wrong that means user is not
    in the chat, so we send him notification

    */
    id = JSON.parse(message).message
    $.getJSON(`/api/v1/message/${id}/`, function (data) {
        if (data.user === currentRecipient ||
            (data.recipient === currentRecipient && data.user === currentUser)) {
            drawMessage(data);
        }
        else if (data.recipient !== currentRecipient) {

            if (!("Notification" in window)) {
                console.log("This browser does not support desktop notification");
            }

            // Let's check whether notification permissions have already been granted
            else if (Notification.permission === "granted") {
                // If it's okay let's create a notification
                var notification = new Notification(data['user'] + " : " + data['body']);
            }

            else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(function (permission) {
                    // If the user accepts, let's create a notification
                    if (permission === "granted") {
                        var notification = new Notification("Hi there!");
                    }
                });
            }
        }else {
            console.log("notification error from browser");
        }

        messageList.animate({scrollTop: messageList.prop('scrollHeight')});
    });
}

function sendMessage(recipient, body) {
    $.post('/api/v1/message/', {
        recipient: recipient,
        body: body
    }).fail(function () {
        alert('Error! Check console!');
    });
}

function drawMessage(message) {
    /*
    we check the message is for the user or recipient, and
    we select the position and append it ti messages
    we get time stamp, and we put it in Date format in js
    */
    let position = 'left';
    const date = new Date(message.timestamp);
    if (message.user === currentUser) position = 'right';
    const messageItem = `
            <li class="message ${position}">
                <div class="avatar">${message.user}</div>
                    <div class="text_wrapper">
                        <div class="text">${message.body}<br>
                            <span class="small">${date}</span>
                    </div>
                </div>
            </li>`;
    $(messageItem).appendTo('#messages');
}







