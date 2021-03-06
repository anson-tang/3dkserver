<div class="ui-state-active"><h3><b>剧情对话数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <!--<button id="new" onclick="$(location).attr('href', '/scene/new');return false;"><span class="ui-icon ui-icon-circle-plus"></span>新增</button>-->
    <button id="export" onclick="$(location).attr('href', '/dialogue/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/dialogue/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/dialogue/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>对话组</th>
        <th>对话ID</th>
        <th>对话类型</th>
        <th>副本ID</th>
        <th>怪物组ID</th>
        <th>怪物难度</th>
        <th>第几波怪</th>
        <th>这波怪第几回合</th>
        <th>这波怪特定怪的ID</th>
        <th>血量百分比</th>
        <th>怪物死亡触发对话</th>
        <th>胜利结算触发对话</th>
        <th>是否记录</th>
        <th>操作</th>
    </tr>
</thead>
<tbody>
%for row in data:
<tr class="gradeA">
    <td>{{row[0]}}</td>
    <td>{{row[1]}}</td>
    <td>{{row[2]}}</td>
    <td>{{row[3]}}</td>
    <td>{{row[4]}}</td>
    <td>{{row[5]}}</td>
    <td>{{row[6]}}</td>
    <td>{{row[7]}}</td>
    <td>{{row[8]}}</td>
    <td>{{row[9]}}</td>
    <td>{{row[10]}}</td>
    <td>{{row[11]}}</td>
    <td>{{row[12]}}</td>
    <td style="width:60px;">
        <button id="delete" style="width:20px;height:20px;" onclick="return dialogue_delete({{row[1]}});"></button>
    </td>
</tr>
%end
</tbody>
</table>
</div>
<div>
<div id="d_content" style="float:left;width:60%;"></div>
</div>
<div style="height:500px;"></div>
%rebase content_base js='dialogue'
