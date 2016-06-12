var oTable;

function vip_chargelist_delete(sid) {
    if (confirm("确定要删除ChargeID [ " + sid + " ]吗?")) {
        $.post('/vip_chargelist/delete', {sid: sid}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/vip_chargelist');
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

function vip_chargedesc_del(cid) {
    if (confirm("确定删除该条描述吗？")) {
        $.post("/vip_chargedesc/deldesc", {cid:cid}, function(result){
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID：" + result.result );
            } else {
                vip_chargedesc_get(cid);
            }   
        }); 
    } else {

    }   
    return false;
}

function vip_chargedesc_get(cid) {
    $.post('/vip_chargedesc/get', {cid: cid}, function(result) {
        $("#d_content").html('<table id="contents" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;text-align:center;">');

        if (!result.result) {
            $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "充值名称"},
                        {"sTitle": "充值描述"},
                        {"sTitle": "操作"}
                    ]
            });
            
            var data_table = $("#contents").dataTable();
            data_table.fnClearTable();
            
            $(result.data).each(function() {
                data_table.fnAddData([
                    $(this)[1],
                    $(this)[2],
                    '</button><button id="ldel" style="width:20px;height:20px;" onclick="return vip_chargedesc_del(' + cid + ');"></button>'
                  ]);

            });
        } else {
            var data_table = $("#contents").dataTable({
                    "sPaginationType": "full_numbers", 
                    "bDestory": true,
                    "bRetrieve": true,
                    "sDom": '<"toolbar">frtip',
                    "aoColumns": [
                        {"sTitle": "充值名称"},
                        {"sTitle": "充值描述"},
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

        var cid = $(this).children().eq(1).text();
        vip_chargedesc_get(cid);
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

