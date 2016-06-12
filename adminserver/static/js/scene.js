var oTable;

function scene_delete(sid) {
    if (confirm("确定要删除副本[ " + sid + " ]吗?")) {
        $.post('/scene/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/scene');
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

function scene_dungeon_del(sid, dung_id) {
    if (confirm("确定删除该条Dungeon吗？")) {
        $.post("/scene/deldungeon", {sid:sid, dung_id:dung_id}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                scene_dungeons_get(sid);
            }   
        }); 
    } else {

    }   
    return false;
}

function scene_reward_del(sid, star_count, star_num) {
    if (confirm("确定删除该条奖励吗？")) {
        $.post("/scene/delreward", {sid:sid, star_count:star_count}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                scene_rewards_get(sid);
            }   
        }); 
    } else {

    }   
    return false;
}

function scene_dungeons_get(sid) {
    $.post('/scene/dungeon/get', {sid: sid}, function(result) {
        $("#d_dungeon").html('<table id="dungeons" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            /*
            $.map(result.data, function(item, idx) {
                item.push('<button id="lnew" style="width:20px;height:20px;" onclick="return building_limit_new();">' +
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return building_limit_del();"></button>');
            });
            */
            $("#dungeons").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "scrollY":200,
                    "scrollX": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "#"},
                        {"sTitle": "顺序"},
                        {"sTitle": "名称"},
                        {"sTitle": "背景"},
                        {"sTitle": "X"},
                        {"sTitle": "Y"},
                        {"sTitle": "类型"},
                        {"sTitle": "对白"},
                        {"sTitle": "上限"},
                        {"sTitle": "掉落"},
                        {"sTitle": "世界掉落ID"},
                        {"sTitle": "怪物宝箱"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#dungeons").dataTable();
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
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return scene_dungeon_del(' + sid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#dungeons").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollY":200,
                    "scrollX": true,
                    "sDom": '<"toolbar">frtip',
                   /* "aaData": [
                                [null, '<font style="color:red;"><b>空</b></font>', 0, 
                                    '<button id="lnew" style="width:20px;height:20px;" onclick="return building_limit_new();"></button>' 
                                ],
                            ],*/
                    "aoColumns": [
                        {"sTitle": "#"},
                        {"sTitle": "顺序"},
                        {"sTitle": "名称"},
                        {"sTitle": "背景"},
                        {"sTitle": "X"},
                        {"sTitle": "Y"},
                        {"sTitle": "类型"},
                        {"sTitle": "对白"},
                        {"sTitle": "上限"},
                        {"sTitle": "掉落"},
                        {"sTitle": "世界掉落ID"},
                        {"sTitle": "怪物宝箱"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });

}

function scene_rewards_get(sid) {
    $.post('/scene/reward/get', {sid: sid}, function(result) {
        $("#d_rewards").html('<table id="rewards" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#rewards").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollY":200,
                    "scrollX": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "星数"},
                        {"sTitle": "奖励内容"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#rewards").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return scene_reward_del(' + sid + ', ' + $(this)[0] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#rewards").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "scrollY":200,
                    "scrollX": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "星数"},
                        {"sTitle": "奖励内容"},
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

        var sid = $(this).children().eq(0).text();

        scene_dungeons_get(sid);
        scene_rewards_get(sid);
    });

    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip','scrollY':300, 'scrollX':true});
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
