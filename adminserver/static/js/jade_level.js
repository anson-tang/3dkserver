var oTable;

function jade_level_delete(sid) {
    if (confirm("确定要删除教程组[ " + sid + " ]吗?")) {
        $.post('/jade_level/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/jade_level');
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
    $("button#delete").button({icons:{primary:"ui-icon-circle-close"}, text:false});
}

function jade_cost_del(sid) {
    if (confirm("确定删除该条guide吗？")) {
        $.post("/jade_level/dellist", {sid:sid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                jade_costs_get(sid);
            }   
        }); 
    } else {

    }   
    return false;
}


function jade_costs_get(sid) {
    $.post('/jade_level/list/get', {sid: sid}, function(result) {
        $("#d_list").html('<table id="lists" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            $("#lists").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "scrollY": 150,
                    "scrollX": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "消耗道具类型"},
                        {"sTitle": "消耗道具ID"},
                        {"sTitle": "消耗道具数量"},
                    ]
            });
            
            var data_table = $("#lists").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    $(this)[2],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return jade_cost_del(' + sid + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#lists").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollY": 150,
                    "scrollX": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "消耗道具类型"},
                        {"sTitle": "消耗道具ID"},
                        {"sTitle": "消耗道具数量"},
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

        var sid = $(this).children().eq(1).text();

        jade_costs_get(sid);
    });

    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip', "scrollY":300, 'scrollX':true});
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
