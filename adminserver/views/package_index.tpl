<div class="ui-state-active"><h3><b>随机礼包数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <button id="export" onclick="$(location).attr('href', '/package/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/package/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/package/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center;">
<thead>
    <tr>
        <th>ID</th>
        <th>礼包ID</th>
        <th>礼包类型</th>
        <th>玩家等级</th>
        <th>VIP等级</th>
        <th>概率</th>
        <th>获得道具类型</th>
        <th>道具ID</th>
        <th>获得数量</th>
        <th>是否公告</th>
        <th>该活动开启时可用</th>
        <th>操作</th>
    </tr>
</thead>
<tbody>
</tbody>
</table>
</div>
<div style="height:500px;"></div>
<script type="text/javascript">
clang = {{lang}};
</script>
%rebase content_base js='package'
