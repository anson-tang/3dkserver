var oTable;

function task_delete(tid) {
    if (confirm("确定要删除任务[ " + tid + " ]吗?")) {
        $.post('/task/delete', {tid: tid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/task');
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

function task_dungeon_del(tid, dung_id) {
    if (confirm("确定删除该条Dungeon吗？")) {
        $.post("/task/deldungeon", {tid:tid, dung_id:dung_id}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                task_dungeons_get(tid);
            }   
        }); 
    } else {

    }   
    return false;
}

function task_dialogue_del(tid, dialog_id) {
    if (confirm("确定删除该条对白吗？")) {
        $.post("/task/deldialogue", {tid:tid, dialog_id:dialog_id}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                task_dialogues_get(tid);
            }   
        }); 
    } else {

    }   
    return false;
}

function task_dungeons_get(tid) {
    $.post('/task/dungeon/get', {tid: tid}, function(result) {
        $("#d_dungeon").html('<table id="dungeons" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#dungeons").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "类型", "sWidth":"10%"},
                        {"sTitle": "值", "sWidth":"10%"},
                        {"sTitle": "对话顺序", "sWidth":"10%"},
                        {"sTitle": "对话NPC", "sWidth":"10%"},
                        {"sTitle": "资源路径", "sWidth":"10%"},
                        {"sTitle": "半身像", "sWidth":"10%"},
                        {"sTitle": "对话"},
                        {"sTitle": "操作", "sWidth":"10%"}
                    ]
            });
            
            var data_table = $("#dungeons").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[2],
                    $(this)[3],
                    $(this)[4],
                    $(this)[5],
                    $(this)[6],
                    $(this)[7],
                    $(this)[8],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return task_dungeon_del(' + tid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#dungeons").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                   /* "aaData": [
                                [null, '<font style="color:red;"><b>空</b></font>', 0, 
                                    '<button id="lnew" style="width:20px;height:20px;" onclick="return building_limit_new();"></button>' 
                                ],
                            ],*/
                    "aoColumns": [
                        {"sTitle": "类型"},
                        {"sTitle": "值"},
                        {"sTitle": "对话顺序"},
                        {"sTitle": "对话NPC"},
                        {"sTitle": "资源路径"},
                        {"sTitle": "半身像"},
                        {"sTitle": "对话"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });

}

function task_dialogues_get(tid) {
    $.post('/task/dialogue/get', {tid: tid}, function(result) {
        $("#d_dialogue").html('<table id="dialogues" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#dialogues").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "类型", "sWidth":"10%"},
                        {"sTitle": "对话顺序", "sWidth":"10%"},
                        {"sTitle": "对话NPC", "sWidth":"10%"},
                        {"sTitle": "资源路径", "sWidth":"10%"},
                        {"sTitle": "半身像", "sWidth":"10%"},
                        {"sTitle": "对话"},
                        {"sTitle": "操作", "sWidth":"10%"}
                    ]
            });
            
            var data_table = $("#dialogues").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[2],
                    $(this)[3],
                    $(this)[4],
                    $(this)[5],
                    $(this)[6],
                    $(this)[7],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return task_dialogue_del(' + tid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#dialogues").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "类型"},
                        {"sTitle": "对话顺序"},
                        {"sTitle": "对话NPC"},
                        {"sTitle": "资源路径"},
                        {"sTitle": "半身像"},
                        {"sTitle": "对话"},
                        {"sTitle": "操作"}
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

        var tid = $(this).children().eq(0).text();

        task_dungeons_get(tid);
        task_dialogues_get(tid);
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
