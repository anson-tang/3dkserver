<div style="overflow-y:scroll;height:800px">
<div class="ui-state-active"><h3><b>TEST</b></h3></div>


<div style="margin:0px 0px 30px 0px;">
<fieldset>
    <table border="0">   
    <tr>
        <td>角色等级：</td><td><input type="text" id="role_level" name="role_level"/></td>
    </tr>
    <tr>
        <td>VIP等级：</td><td><input type="text" id="vip_level" name="vip_level"/></td>
    </tr>
    <tr>
        <td>随机次数(1-100万)：</td><td><input type="text" id="count" name="count"/></td>
    </tr>
    <tr>
        <td><button id="btn_random_item" onclick="return random_item_js();">我要翻你牌</button></td>
    </tr>
    </table>
</fieldset>
</div>

<div style="margin:0px 0px 30px 0px;">
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>#</th>
        <th>角色等级</th>
        <th>VIP等级</th>
        <th>道具类型</th>
        <th>道具ID</th>
        <th>道具数量</th>
        <th>权重</th>
        <th>递增权重</th>
        <th>活动ID</th>
        <th>抽中次数</th>
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
</tr>
%end
</tbody>
</table>
</div>

</div>
      
%rebase content_base js="test"
