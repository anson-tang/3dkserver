var oTable;

function fellow_delete(fid) {
    if (confirm("确定要删除伙伴[ " + fid + " ]吗?")) {
        $.post('/fellow/delete', {fid: fid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/fellow');
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

function fellow_decomposition_del(qlevel) {
    if (confirm("确定删除该条分解类型吗？")) {
        $.post("/fellow/deldecomposition", {qlevel:qlevel}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                fellow_decomposition_get(qlevel);
            }   
        }); 
    } else {

    }   
    return false;
}

function fellow_reborn_del(qlevel) {
    if (confirm("确定删除该条重生配置吗？")) {
        $.post("/fellow/delreborn", {qlevel:qlevel}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                fellow_reborn_get(qlevel);
            }   
        }); 
    } else {

    }   
    return false;
}

function fellow_decomposition_get(qlevel) {
    $.post('/fellow/decomposition/get', {qlevel: qlevel}, function(result) {
        $("#d_decomposition").html('<table id="decompositions" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#decompositions").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "伙伴品级"},
                        {"sTitle": "分解产物列表"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#decompositions").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return fellow_decomposition_del(' + qlevel + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#decompositions").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "伙伴品级"},
                        {"sTitle": "分解产物列表"},
                        {"sTitle": "操作"}
                    ]
            });
            data_table.fnClearTable();
        }

        $("button#ldel").button({icons:{primary:"ui-icon-circle-minus"}, text:false});
    });

}

function fellow_reborn_get(qlevel) {
    $.post('/fellow/reborn/get', {qlevel: qlevel}, function(result) {
        $("#d_reborn").html('<table id="reborns" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#reborns").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "品级"},
                        {"sTitle": "进阶次数"},
                        {"sTitle": "重生所需钻石"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#reborns").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[0],
                    $(this)[1],
                    $(this)[2],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return fellow_reborn_del(' + qlevel + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#reborns").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "品级"},
                        {"sTitle": "进阶次数"},
                        {"sTitle": "重生所需钻石"},
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

        var qlevel  = $(this).children().eq(8).text();

        fellow_decomposition_get(qlevel);
        fellow_reborn_get(qlevel);
    });

    oTable = $("#data").dataTable({"sPaginationType": "full_numbers", "sDom": '<"toolbar">frtip', "scrollY":400, "scrollX":true});
    $("button#export").button();
    $("button#import").button();
    $("button#save").button();
    $("button#del").button();
    $("button#back").button();
    $("button#recover").button();
    render_btn();
});
