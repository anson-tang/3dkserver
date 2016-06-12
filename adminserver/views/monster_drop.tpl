<div class="ui-state-active"><h3><b>副本怪物掉落数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <button id="export" onclick="$(location).attr('href', '/monster_drop/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/monster_drop/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/monster_drop/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>
<div style="height:20px;">
</div>
<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center">
<thead>
    <tr>
        <th>掉落ID</th>
        <th>怪物小队ID</th>
        <th>怪物小队难度</th>
        <th>道具类型</th>
        <th>道具ID</th>
        <th>初始掉落概率(万分比)</th>
        <th>单次增加概率(万分比)</th>
        <th>单次封顶概率(万分比)</th>
        <th>道具数量</th>
        <th>任务ID</th>
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
%rebase content_base js='monster_drop'
