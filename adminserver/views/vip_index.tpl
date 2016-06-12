<div class="ui-state-active"><h3><b>VIP等级数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <button id="export" onclick="$(location).attr('href', '/vip/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/vip/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/vip/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>VIP等级</th>
        <th>需要充值金额</th>
        <th>强化暴击最大倍率</th>
        <th>天外天免费挑战次数</th>
        <th>天外天免费重置次数</th>
        <th>天外天可购买重置次数</th>
        <th>精英副本可购买次数</th>
        <th>活动副本可购买次数</th>
        <th>副本扫荡CD时间</th>
        <th>自动战斗开关</th>
        <th>剧情副本跳过战斗开关</th>
        <th>精英副本跳过战斗开关</th>
        <th>活动副本跳过战斗开关</th>
        <th>天外天跳过战斗开关</th>
        <th>世界BOSS自动开关</th>
        <th>最大连战次数</th>
        <th>神秘商店免费最大刷新次数</th>
        <th>神秘商店购买最大刷新次数</th>
        <th>仙盟女娲宫每日最大钻石拜祭次数</th>
        <th>副本全扫荡开关</th>
        <th>大乱斗可购买次数</th>
        <th>皇陵探宝免费次数</th>
        <th>剧情副本挑战可重置次数</th>
        <th>宝物碎片十连抢开关</th>
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
    <td style="width:60px;">
        <button id="delete" style="width:20px;height:20px;" onclick="return vip_delete({{row[0]}});"></button>
    </td>
</tr>
%end
</tbody>
</table>
</div>
<div style="height:500px;"></div>
%rebase content_base js='vip'
