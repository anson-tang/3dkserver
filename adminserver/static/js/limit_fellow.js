var oTable;

function limit_fellow_delete(aid) {
    if (confirm("确定要删除AttributeID [ " + aid + " ]吗?")) {
        $.post('/limit_fellow/delete', {aid: aid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/limit_fellow');
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

function limit_fellow_desc_del(aid, turn_id) {
    if (confirm("确定删除该条描述吗？" )) {
        $.post('/limit_fellow/deldesc', {turn_id:turn_id}, function(result){
            if (result.result) {
                alert("删除失败! 原因: " + result.data + ", ID: " + result.result);
            } else {
                limit_fellow_desc_get(aid);
            }
        });
    } else {
    }
    return false;
}

function limit_fellow_desc_get(aid) {
    $.post('/limit_fellow/desc/get', {aid: aid}, function(result) {
        $("#d_desc").html('<table id="contents" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "顺序"},
                        {"sTitle": "说明"},
                    ]
            });

            var data_table = $("#contents").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return limit_fellow_desc_del(' + aid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "顺序"},
                        {"sTitle": "说明"},
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
        limit_fellow_desc_get(aid);
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
