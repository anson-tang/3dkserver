var oTable;

function dialogue_delete(mid) {
    if (confirm("确定要删除Monster[ " + mid + " ]吗?")) {
        $.post('/dialogue/delete', {mid: mid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/dialogue');
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

function dialogue_content_del(mid, turn_id) {
    if (confirm("确定删除该条Monster Attribute吗？")) {
        $.post("/dialogue/delcontent", {turn_id:turn_id}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                dialogue_content_get(mid);
            }   
        }); 
    } else {

    }   
    return false;
}

function dialogue_content_get(mid) {
    $.post('/dialogue/content/get', {mid: mid}, function(result) {
        $("#d_content").html('<table id="contents" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollX":true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "对话顺序"},
                        {"sTitle": "NPC"},
                        {"sTitle": "NPC的名字"},
                        {"sTitle": "NPC位置"},
                        {"sTitle": "NPC半身像"},
                        {"sTitle": "半身像偏移量X"},
                        {"sTitle": "半身像偏移量Y"},
                        {"sTitle": "对话内容"},
                        {"sTitle": "是否切换场景"},
                        {"sTitle": "是否切换音乐"},
                        {"sTitle": "是否改变阵容"},
                        {"sTitle": "乱入怪物ID"},
                        {"sTitle": "乱入怪物属性ID"},
                        {"sTitle": "是否强制胜利"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#contents").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
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
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return dialogue_content_del(' + mid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollX":true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "对话顺序"},
                        {"sTitle": "NPC"},
                        {"sTitle": "NPC位置"},
                        {"sTitle": "NPC半身像"},
                        {"sTitle": "半身像偏移量X"},
                        {"sTitle": "半身像偏移量Y"},
                        {"sTitle": "对话内容"},
                        {"sTitle": "是否切换场景"},
                        {"sTitle": "是否切换音乐"},
                        {"sTitle": "是否改变阵容"},
                        {"sTitle": "乱入怪物ID"},
                        {"sTitle": "乱入怪物属性ID"},
                        {"sTitle": "是否强制胜利"},
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

        var mid = $(this).children().eq(1).text();
        dialogue_content_get(mid);
    });

    oTable = $("#data").dataTable({
        "sPaginationType": "full_numbers", 
                   "sDom": '<"toolbar">frtip', 
                'scrollX':true,
    });

    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
