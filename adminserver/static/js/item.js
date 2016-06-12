var oTable;
var c_lang = 0

function item_delete(iid) {
    if (confirm("确定要删除道具[ " + iid + " ]吗?")) {
        $.post('/item/delete', {iid: iid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/item');
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

function item_attribute_del(iid, aid) {
    if (confirm("确定删除该条属性吗？")) {
        $.post("/item/delattribute", {iid:iid, aid:aid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                item_attribute_get(iid);
            }   
        }); 
    } else {

    }   
    return false;
}

function item_treasureunlock_del(iid, aid) {
    if (confirm("确定删除该条属性吗？")) {
        $.post("/item/deltreasureunlock", {iid:iid, aid:aid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                item_treasureunlock_get(iid);
            }   
        }); 
    } else {

    }   
    return false;
}

function fellow_changeitem_del(iid, siid) {
    if (confirm("确定删除该条配置吗？")) {
        $.post("/item/delchangeitem", {iid:iid, siid:siid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                item_reborn_get(iid);
            }   
        }); 
    } else {

    }   
    return false;
}

function item_attribute_get(iid) {
    $.post('/item/attribute/get', {iid: iid}, function(result) {
        $("#d_attribute").html('<table id="attributes" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            $("#attributes").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "属性ID"},
                        {"sTitle": "值"},
                        {"sTitle": "每次强化上升"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#attributes").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    $(this)[3],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return item_attribute_del(' + iid + ',' + $(this)[1] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#attributes").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "属性ID"},
                        {"sTitle": "值"},
                        {"sTitle": "每次强化上升"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });

}

function item_changeitem_get(iid) {
    $.post('/item/changeitem/get', {iid: iid}, function(result) {
        $("#d_changeitem").html('<table id="changeitems" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            $("#changeitems").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "消耗道具ID"},
                        {"sTitle": "数量"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#changeitems").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return item_changeitem_del(' + iid + ',' + $(this)[1] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#changeitems").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "消耗道具ID"},
                        {"sTitle": "数量"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });
}

function item_treasureunlock_get(iid) {
    $.post('/item/treasureunlock/get', {iid: iid}, function(result) {
        $("#d_treasureunlock").html('<table id="treasureunlocks" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0">');

        if (!result.result) {
            $("#treasureunlocks").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "解锁属性等级"},
                        {"sTitle": "属性ID"},
                        {"sTitle": "属性值"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#treasureunlocks").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    $(this)[3],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return item_treasureunlock_delete(' + iid + ',' + $(this)[1] + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#treasureunlocks").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "解锁属性等级"},
                        {"sTitle": "属性ID"},
                        {"sTitle": "属性值"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });
}

function onRowCallback(row, data) {
    $(row).click(function (e) {
        if ($(this).hasClass('row_selected')) {
            $(this).removeClass('row_selected');
        } else {
            oTable.$('tr.row_selected').removeClass('row_selected');
            $(this).addClass('row_selected');
        }

        var iid = $(this).children().eq(0).text();
        //console.log('here...', iid);
        item_attribute_get(iid);
        item_treasureunlock_get(iid);
    });
}

$(function() {
    /*
    $("#data tbody ").click(function (e) {
        if ($(this).hasClass('row_selected')) {
            $(this).removeClass('row_selected');
        } else {
            oTable.$('tr.row_selected').removeClass('row_selected');
            $(this).addClass('row_selected');
        }


        var iid  = $(this).children().eq(0).text();
        item_attribute_get(iid);
        item_treasureunlock_get(iid);
    });
    */
    oTable = $("#data").dataTable({
        "sPaginationType": "full_numbers", 
        "bProcessing":true,
        "bServerSide":true,
        "sAjaxSource":"/item/page",
        "rowCallback":onRowCallback,
        "sDom": '<"toolbar">frtip', 
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
