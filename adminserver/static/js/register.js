function regist() {
    var server= $("#server").val();
    var username = $("#username").val();
    var password = $("#password").val();
    var ch_password = $("#ch_password").val();
        
    if (password != ch_password){
        alert("密码输入不一致");
        return false;        
    }   
        
    $.post('/register', {username:username,password:password,server:server}, function(result){
            if (result.result) { 
                alert('注册失败。原因：' + result.data + ', ID: ' + result.result);
            } else {
                alert('注册成功');   
            }
        });
    return false;
}       
        
function check_passwd(){
    var password = $("#password").val();
    var ch_password = $("#ch_password").val();
        
    if (password != ch_password){
        $("#show_msg").html("<strong>密码不一致</strong>"); 
        $("#show_msg").attr("style", "color:red");
    }   
    else {
        $("#show_msg").html("<b>密码一致，请点击'注册'</b>");
        $("#show_msg").attr("style", "color:green");
    }   
}       
        
$(function() {
    $('button#regist').button();
});     
