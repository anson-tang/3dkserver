function sync_daily_server() {
    $.post('/sync_daily_server',{'delay':0}, function(result){
        alert('执行反馈：\n' + result.out1);
    });
    return false;
}

$(function() {
    $('button#btn_sync_daily_server').button();
});
