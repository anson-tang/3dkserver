function reboot_server() {
    $.post('/reboot_server',{'delay':0}, function(result){
        alert('执行反馈：\n' + result.out1);
    });
    return false;
}

$(function() {
    $('button#btn_reboot_server').button();
});
