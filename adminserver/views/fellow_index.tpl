<div class="ui-state-active"><h3><b>伙伴数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <!--<button id="new" onclick="$(location).attr('href', '/scene/new');return false;"><span class="ui-icon ui-icon-circle-plus"></span>新增</button>-->
    <button id="export" onclick="$(location).attr('href', '/fellow/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/fellow/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/fellow/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display" width="100%" cellspacing="0" cellpadding="0" style="text-align:center;">
<thead>
    <tr>
        <th>#</th>
        <th>名称</th>
        <th>伙伴简介</th>
        <th>模型缩放比例</th>
        <th>X偏移</th>
        <th>Y偏移</th>
        <th>星级</th>
        <th>品质</th>
        <th>品级</th>
        <th>伙伴类型</th>
        <th>是否需要单镜头</th>
        <th>等级</th>
        <th>经验</th>
        <th>进阶次数</th>
        <th>道具兑换武将</th>
        <th>资源组</th>
        <th>资源路径</th>
        <th>ICON路径</th>
        <th>阵营</th>
        <th>先手值</th>
        <th>攻击</th>
        <th>攻击名字</th>
        <th>攻击描述</th>
        <th>技能攻击</th>
        <th>技能名字</th>
        <th>技能描述</th>
        <th>待机音效</th>
        <th>普攻音效</th>
        <th>技能音效</th>
        <th>受击音效</th>
        <th>废话音效</th>
        <th>武力</th>
        <th>智力</th>
        <th>当前生命值</th>
        <th>最大生命值</th>
        <th>每级增加(生)</th>
        <th>初始怒气</th>
        <th>攻击类型</th>
        <th>攻击</th>
        <th>每级增加(供给)</th>
        <th>物理防御</th>
        <th>每级增加(防)</th>
        <th>法术防御</th>
        <th>每级增加(法)</th>
        <th>暴击率</th>
        <th>暴击抗性</th>
        <th>暴击伤害</th>
        <th>抗暴伤</th>
        <th>格挡</th>
        <th>破击</th>
        <th>反击</th>
        <th>抗反击</th>
        <th>命中</th>
        <th>闪避</th>
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
    <td>{{row[31]}}</td>
    <td>{{row[32]}}</td>
    <td>{{row[33]}}</td>
    <td>{{row[34]}}</td>
    <td>{{row[35]}}</td>
    <td>{{row[36]}}</td>
    <td>{{row[37]}}</td>
    <td>{{row[38]}}</td>
    <td>{{row[39]}}</td>
    <td>{{row[40]}}</td>
    <td>{{row[41]}}</td>
    <td>{{row[42]}}</td>
    <td>{{row[43]}}</td>
    <td>{{row[44]}}</td>
    <td>{{row[45]}}</td>
    <td>{{row[46]}}</td>
    <td>{{row[47]}}</td>
    <td>{{row[48]}}</td>
    <td>{{row[49]}}</td>
    <td>{{row[50]}}</td>
    <td>{{row[51]}}</td>
    <td>{{row[52]}}</td>
    <td>{{row[53]}}</td>
    <td style="width:60px;">
        <button id="delete" style="width:20px;height:20px;" onclick="return fellow_delete({{row[0]}});"></button>
    </td>
</tr>
%end
</tbody>
</table>
</div>
<div>
<div id="d_decomposition" style="float:left;width:60%;"></div>
<div id="d_reborn" style="float:right;width:39%;"></div>
</div>
<div style="height:500px;"></div>
%rebase content_base js='fellow'
