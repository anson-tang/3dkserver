var oTable;
var c_lang = 0;

function monster_drop_delete(sid) {
    if (confirm("确定要删除Skill ball[ " + sid + " ]吗?")) {
        $.post('/monster_drop/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/monster_drop');
            }
        });
    }

    return false;
}

function upload() {
    var name = $('#csv').val();
    var arr_name = name.split('.');

    if (!name) {
        alert('错误，上传文件为空!');
    } else if ((arr_name[arr_name.length - 1]).toLowerCase() != 'csv') {
        alert('错误，只支持CSV文件格式!');
    } else if (confirm("此操作会覆盖服务器上所有数据，您确定要导入吗？")) {
        $("#upload").submit();
    }
    return false;    
}

function render_btn() {
    //$("button#edit").button({icons:{primary:"ui-icon-folder-open"}, text:false});
    $("button#delete").button({icons:{primary:"ui-icon-circle-close"}, text:false});
}

$(function() {
    $("#data tbody tr").click(function (e) {
        if ($(this).hasClass('row_selected')) {
            $(this).removeClass('row_selected');
        } else {
            oTable.$('tr.row_selected').removeClass('row_selected');
            $(this).addClass('row_selected');
        }
    });

    oTable = $("#data").dataTable({
        "sPaginationType": "full_numbers", 
        "sDom": '<"toolbar">frtip',
        "bProcessing":true,
        "bServerSide":true,
        "sAjaxSource":"monster_drop/page",
        "scrollY":400,
        "scrollX":true
    });
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
