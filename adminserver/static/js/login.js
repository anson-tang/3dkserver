function login() {
    var name = $("#username").val();
    if (!name){
        alert("账号未填");
        return false;
    }

    var passwd = $("#password").val();
    if (!passwd){
        alert("密码未填");
        return false;
    }

    $('#frm_login').submit();

    return false;
}

$(function() {
    $("#btn_login").button();
});
