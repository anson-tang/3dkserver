<div style="overflow-y:scroll;height:800px">
<div class="ui-state-active"><h3><b>多语言</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <button id="export" onclick="$(location).attr('href', '/keyword/export/{{lang}}');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="kupload" action="/keyword/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <select id="lang" name="lang" style="width:152px">
        <option value="-1" 'selected'>未选择</option>
        <option value="0">源</option>
        %for lang_id, lang_name in all_lang:
        <option value="{{lang_id}}">{{lang_name}}</option>
        %end
    </select>
    <button id="import" href="#" onclick="return keyword_import();"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    </form>
    </div>
    <div style="float:right;padding-top:20px;">
    <label>当前语言：</label>
    <select id="c_lang" name="c_lang" style="width:152px">
        <option value="0" 'selected'>源</option>
        %for lang_id, lang_name in all_lang:
        <option value="{{lang_id}}">{{lang_name}}</option>
        %end
    </select>
    </div>
</div>
<div style="height:20px;">
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center">
<thead>
    <tr>
        <th>多语言_键</th>
        <th>多语言_值</th>
        <th style="width:60px;">操作</th>
    </tr>
</thead>
<tbody>
</tbody>
</table>
</div>
</div>
<script type="text/javascript">
c_lang = {{lang}};
$("#c_lang").find("option[value='{{lang}}']").attr("selected",true);
</script>
%rebase content_base js='keyword'
