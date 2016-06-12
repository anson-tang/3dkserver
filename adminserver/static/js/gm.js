function exe_gm_cmd_js() {
    var cmd_cmd = $('#cmd_help_list').val();
    var svc     = $('#svc option:selected').val();
    var cmd_args = $("#cmd_args").val();


    $.post('/exe_gm_cmd', { svc:svc, cmd_cmd:cmd_cmd, cmd_args:cmd_args },function(result){
            alert('执行结果：' + result.data);
    });
    return false;
}

function payment() {
    var account = $('#account').val();
    var svc     = $('#svc1 option:selected').val();
    var credits = $("#charge_id").val();


    $.post('/payment', { svc:svc, account:account, charge_id:charge_id},function(result){
            alert('执行结果：' + result.data);
    });
    return false;
}


$(function() {
    $('button#btn_gm_cmd').button();
    $('button#btn_payment').button();
});
