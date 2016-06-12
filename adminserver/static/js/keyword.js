var oTable;
var c_lang = 0;

function keyword_delete(key) {
    if (confirm("确定要删除[ " + key + " ]吗?")) {
        $.post('/keyword/delete', {key: key}, function(result) {
            if (result.result) {
                alert("删除失败！原因：" + result.data + ", ID: " + result.result);    
            } else {
                $(location).attr('href', '/keyword');
            }
        });
    }

    return false;
}

function keyword_import(){
    var selected_idx = $('#lang option:selected').index();
    if (selected_idx && selected_idx > 0){
        $('#kupload').submit();
    } else {
        alert("清选择语言先!");
    }

    return false;
}

function render_btn() {
    //$("button#edit").button({icons:{primary:"ui-icon-folder-open"}, text:false});
    $("button#delete").button({icons:{primary:"ui-icon-circle-close"}, text:false});
}

function append_param_lang( aoData ) {
    aoData.push( { "name":"lang", "value":c_lang } );
}

function change_current_language() {
    c_lang = $(this).val();
    oTable.fnDestroy();

    oTable = $('#data').dataTable({
        'sPaginationType': 'full_numbers',
        'bProcessing': true,
        'bServerSide': true,
        'sAjaxSource': '/keyword/page',
        'fnServerParams': append_param_lang,
        "scrolY": "400px",
        "scrolCollapse": "true"
    });

    $('#export').click(function(){
        $(location).attr('href', '/keyword/export/' + c_lang);
        return false;
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
    });

    oTable = $("#data").dataTable({
        "sPaginationType": "full_numbers", 
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": "/keyword/page",
        "fnServerParams": append_param_lang,
        "scrolY": "400px",
        "scrolCollapse": "true"
    });

    $("button#export").button();
    $("button#import").button();
    $("button#del").button();
    $("button#back").button();
    render_btn();

    $("select#c_lang").change(change_current_language);
});
