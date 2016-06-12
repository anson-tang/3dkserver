var oTable;

function activescene_delete(sid) {
    if (confirm("确定要删除副本[ " + sid + " ]吗?")) {
        $.post('/activescene/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/activescene');
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

function activescene_monster_del(sid, tid) {
    if (confirm("确定删除该条Dungeon吗？")) {
        $.post("/activescene/delmonster", {sid:sid, tid:tid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                activescene_monsters_get(sid);
            }   
        }); 
    } else {

    }   
    return false;
}


function activescene_monsters_get(sid) {
    $.post('/activescene/monster/get', {sid: sid}, function(result) {
        $("#d_monster").html('<table id="monsters" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            $("#monsters").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "scrollX": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "怪物波次"},
                        {"sTitle": "是否是Boss"},
                        {"sTitle": "怪物模型列表"},
                        {"sTitle": "怪物属性列表"},
                    ]
            });
            
            var data_table = $("#monsters").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    $(this)[2],
                    $(this)[3],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return activescene_monster_del(' + sid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#monsters").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollX": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "怪物波次"},
                        {"sTitle": "是否是Boss"},
                        {"sTitle": "怪物模型列表"},
                        {"sTitle": "怪物属性列表"},
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

        activescene_monsters_get(sid);
    });

    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip','scrollX':true});
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
