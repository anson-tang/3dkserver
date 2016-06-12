var oTable;

function newbieguide_delete(sid) {
    if (confirm("确定要删除教程组[ " + sid + " ]吗?")) {
        $.post('/newbieguide/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/newbieguide');
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

function newbieguide_list_del(sid, tid) {
    if (confirm("确定删除该条guide吗？")) {
        $.post("/newbieguide/dellist", {sid:sid, tid:tid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                newbieguide_lists_get(sid);
            }   
        }); 
    } else {

    }   
    return false;
}


function newbieguide_lists_get(sid) {
    $.post('/newbieguide/list/get', {sid: sid}, function(result) {
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
                        {"sTitle": "顺序ID"},
                        {"sTitle": "出现NPC的半身像"},
                        {"sTitle": "提示文字"},
                        {"sTitle": "NPC出现的位置"},
                        {"sTitle": "箭头位置"},
                        {"sTitle": "跳转类型"},
                        {"sTitle": "界面ID"},
                        {"sTitle": "按钮名"},
                        {"sTitle": "副本ID"},
                        {"sTitle": "开始位置X"},
                        {"sTitle": "开始位置Y"},
                        {"sTitle": "宽"},
                        {"sTitle": "高"},
                        {"sTitle": "是否记录"},
                        {"sTitle": "引导配音"},
                    ]
            });
            
            var data_table = $("#lists").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    $(this)[2],
                    $(this)[3],
                    $(this)[4],
                    $(this)[5],
                    $(this)[6],
                    $(this)[7],
                    $(this)[8],
                    $(this)[9],
                    $(this)[10],
                    $(this)[11],
                    $(this)[12],
                    $(this)[13],
                    $(this)[14],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return newbieguide_list_del(' + sid + ', ' + $(this)[0] + ');"></button>'
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
                        {"sTitle": "顺序ID"},
                        {"sTitle": "出现NPC的半身像"},
                        {"sTitle": "提示文字"},
                        {"sTitle": "NPC出现的位置"},
                        {"sTitle": "箭头位置"},
                        {"sTitle": "跳转类型"},
                        {"sTitle": "界面ID"},
                        {"sTitle": "按钮名"},
                        {"sTitle": "副本ID"},
                        {"sTitle": "开始位置X"},
                        {"sTitle": "开始位置Y"},
                        {"sTitle": "宽"},
                        {"sTitle": "高"},
                        {"sTitle": "是否记录"},
                        {"sTitle": "引导配音"},
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

        var sid = $(this).children().eq(0).text();

        newbieguide_lists_get(sid);
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
