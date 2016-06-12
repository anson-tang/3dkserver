<div class="ui-state-active"><h3><b>副本数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <!--<button id="new" onclick="$(location).attr('href', '/scene/new');return false;"><span class="ui-icon ui-icon-circle-plus"></span>新增</button>-->
    <button id="export" onclick="$(location).attr('href', '/scene/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/scene/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/scene/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>#</th>
        <th>副本名称</th>
        <th>加载资源名</th>
        <th>背景图路径</th>
        <th>背景音乐</th>
        <th>玩家等级限制</th>
        <th>前置副本ID</th>
        <th>最大星数</th>
        <th>副本难度</th>
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
    <td style="width:60px;">
        <!--<button id="edit" style="width:20px;height:20px;"
        onclick="$(location).attr('href','/soldier/edit/{{row[0]}}');return false;"></button>-->
        <button id="delete" style="width:20px;height:20px;" onclick="return scene_delete({{row[0]}});"></button>
    </td>
</tr>
%end
</tbody>
</table>
</div>
<div>
<div id="d_dungeon" style="float:left;width:60%;"></div>
<div id="d_rewards" style="float:right;width:39%;"></div>
</div>
<div style="height:500px;"></div>
%rebase content_base js='scene'
