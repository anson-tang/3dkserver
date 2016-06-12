<div class="ui-state-active"><h3><b>怪物资源数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <!--<button id="new" onclick="$(location).attr('href', '/scene/new');return false;"><span class="ui-icon ui-icon-circle-plus"></span>新增</button>-->
    <button id="export" onclick="$(location).attr('href', '/monstervalue/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/monstervalue/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/monstervalue/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>#</th>
        <th>名称</th>
        <th>偏移X</th>
        <th>偏移Y</th>
        <th>模型的缩放倍率</th>
        <th>资源组</th>
        <th>资源位置</th>
        <th>怪物ICON</th>
        <th>阵营</th>
        <th>BOSS</th>
        <th>怪物品质</th>
        <th>普通攻击动作</th>
        <th>技能攻击动作</th>
        <th>技能名字</th>
        <th>受击等待时间</th>
        <th>待机音效</th>
        <th>普攻音效</th>
        <th>技能音效</th>
        <th>受击音效</th>
        <th>攻击类型</th>
        <th>暴击</th>
        <th>暴击抗性</th>
        <th>暴击伤害</th>
        <th>抗暴伤</th>
        <th>格挡</th>
        <th>破击</th>
        <th>反击</th>
        <th>抗反击</th>
        <th>命中</th>
        <th>闪避</th>
        <th>飘字类型</th>
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
    <td>{{row[13]}}</td>
    <td>{{row[14]}}</td>
    <td>{{row[15]}}</td>
    <td>{{row[16]}}</td>
    <td>{{row[17]}}</td>
    <td>{{row[18]}}</td>
    <td>{{row[19]}}</td>
    <td>{{row[20]}}</td>
    <td>{{row[21]}}</td>
    <td>{{row[22]}}</td>
    <td>{{row[23]}}</td>
    <td>{{row[24]}}</td>
    <td>{{row[25]}}</td>
    <td>{{row[26]}}</td>
    <td>{{row[27]}}</td>
    <td>{{row[28]}}</td>
    <td>{{row[29]}}</td>
    <td>{{row[30]}}</td>
    <td style="width:60px;">
        <!--<button id="edit" style="width:20px;height:20px;"
        onclick="$(location).attr('href','/soldier/edit/{{row[0]}}');return false;"></button>-->
        <button id="delete" style="width:20px;height:20px;" onclick="return monstervalue_delete({{row[0]}});"></button>
    </td>
</tr>
%end
</tbody>
</table>
</div>
<div style="height:500px;"></div>
%rebase content_base js='monstervalue'
