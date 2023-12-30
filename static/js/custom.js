function sendAuthenticationToken() {
    const phone = document.getElementById("phone").value;
    const tokenInput = document.getElementById("token");
    const label_token = document.getElementById("token_label");
    const first_btn = document.getElementById("first_btn");
    const second_btn = document.getElementById("second_btn");
    $.ajax({
        url: "/send-token/",
        data: {phone_no: phone},
        datatype: "json",
        method: "POST",
        beforeSend: function (xhr) {
            const csrftoken = Cookies.get("csrftoken");
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        success: function (res) {
            if (res.status === "success") {
                tokenInput.classList.remove("display-n");
                label_token.classList.remove("display-n");
                first_btn.classList.add("display-n");
                second_btn.classList.remove("display-n");
                alert(res.token);
            }
        },
        error:function (){
            alert("connection failed");
        }
    });
}

function checkAuthenticationToken() {
    const phone = document.getElementById("phone").value;
    const tokenInput = document.getElementById("token").value;

    $.ajax({
        url: "/check-token/",
        data: {phone_no: phone, token: tokenInput},
        datatype: "json",
        method: "POST",
        beforeSend: function (xhr) {
            const csrftoken = Cookies.get("csrftoken");
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        success: function (res) {
            if (res.status === "success") {
                window.location.assign("http://127.0.0.1:8000/");
            }else{
                console.log("Not Nice");
            }

        },
    });

}


function SignUpCheck(){
        const username = document.getElementById('username').value;
        const name = document.getElementById('name').value;
        const phone_no = document.getElementById('phone-no').value;
        const role = document.getElementById('role').value;
        const company = document.getElementById('company').value;
        // const remind_me = $('#remind-me').is(':checked');

        $.ajax({
        url: "/sign-up/",
        data: {
            username:username,
            name:name,
            phone_no:phone_no,
            role:role,
            company:company,

        },
        datatype: "json",
        method: "POST",
        beforeSend: function (xhr) {
            const csrftoken = Cookies.get("csrftoken");
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        success: function (res) {
            if (res.status === "success") {
                window.location.assign("http://127.0.0.1:8000/");
            }else{
                console.log("Not Nice");
            }

        },
        error:function (res){
          alert('Connection Failed');

          },
    });
}