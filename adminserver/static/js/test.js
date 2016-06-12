
var oTable;

function random_item_js() {
    var role_level = $('#role_level').val();
    var vip_level  = $('#vip_level').val();
    var count      = $('#count').val();

    $.post('/random_item', {cmd:'test_random_item', count:count, vip_level:vip_level, role_level:role_level}, function(result){ 
//            if (result.result) {
//                alert('result:' + result.data);
//            } else {
                $(location).attr('href', '/test');
//            }
    });

    return false;
}


$(function() {
    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip'});
});




