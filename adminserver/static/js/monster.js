var oTable;

function monster_delete(mid) {
    if (confirm("确定要删除Monster[ " + mid + " ]吗?")) {
        $.post('/monster/delete', {mid: mid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/monster');
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

function monster_attr_del(mid, attr_id) {
    if (confirm("确定删除该条Monster Attribute吗？")) {
        $.post("/monster/delattr", {attr_id:attr_id}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                monster_attr_get(mid);
            }   
        }); 
    } else {

    }   
    return false;
}

function monster_attr_get(mid) {
    $.post('/monster/attr/get', {mid: mid}, function(result) {
        $("#d_attr").html('<table id="attrs" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#attrs").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "怪物列表"},
                        {"sTitle": "属性列表"},
                        {"sTitle": "顺序"},
                        {"sTitle": "是否是boss"},
                        {"sTitle": "背景图"},
                        {"sTitle": "每波怪物的音乐"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#attrs").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    $(this)[3],
                    $(this)[4],
                    $(this)[5],
                    $(this)[6],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return monster_attr_del(' + mid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#attrs").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "怪物列表"},
                        {"sTitle": "属性列表"},
                        {"sTitle": "顺序"},
                        {"sTitle": "背景图"},
                        {"sTitle": "每波怪物的音乐"},
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

        var mid = $(this).children().eq(0).text();
        monster_attr_get(mid);
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
