var oTable;

function lucky_turntable_delete(aid) {
    if (confirm("确定要删除type [ " + aid + " ]吗?")) {
        $.post('/lucky_turntable/delete', {aid: aid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/lucky_turntable');
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

function lucky_turntable_item_del(aid, turn_id) {
    if (confirm("确定删除该条描述吗？" )) {
        $.post('/lucky_turntable/delitem', {turn_id:turn_id}, function(result){
            if (result.result) {
                alert("删除失败! 原因: " + result.data + ", ID: " + result.result);
            } else {
                lucky_turntable_item_get(aid);
            }
        });
    } else {
    }
    return false;
}

function lucky_turntable_item_get(aid) {
    $.post('/lucky_turntable/item/get', {aid: aid}, function(result) {
        $("#d_item").html('<table id="contents" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "道具类型"},
                        {"sTitle": "道具ID"},
                        {"sTitle": "道具数量"},
                    ]
            });

            var data_table = $("#contents").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[2],
                    $(this)[3],
                    $(this)[4],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return lucky_turntable_item_del(' + aid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "道具类型"},
                        {"sTitle": "道具ID"},
                        {"sTitle": "道具数量"},
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });
}




$(function() {
    $("#data tbody tr").click(function (e) {
        if ($(this).hasClass('row_selected')) {
            $(this).removeClass('row_selected');
        } else {
            oTable.$('tr.row_selected').removeClass('row_selected');
            $(this).addClass('row_selected');
        }

        var aid = $(this).children().eq(0).text();
        lucky_turntable_item_get(aid);
    });


    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip'});
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
