<div class="ui-state-active"><h3><b>道具数值管理</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
    <div style="float:left;">
    <!--<button id="new" onclick="$(location).attr('href', '/scene/new');return false;"><span class="ui-icon ui-icon-circle-plus"></span>新增</button>-->
    <button id="export" onclick="$(location).attr('href', '/item/export');return false;"><span class="ui-icon ui-icon-circle-arrow-s"></span>全表导出</button>
    </div>
    <div style="float:left;margin-left:20px;">
    <form id="upload" action="/item/import" method="POST" enctype="multipart/form-data">
    <input type="file" name="data" id="csv"/>
    <button id="import"><span class="ui-icon ui-icon-circle-arrow-n"></span>全表导入</button>
    <button id="recover" onclick="$(location).attr('href', '/item/recover');return false;"><span class="ui-icon ui-icon-circle-arrow-n"></span>恢复</button>
    </form>
    </div>
</div>

<table id="data" class="display dataTable" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:
100%;text-align:center">
<thead>
    <tr>
        <th>#</th>
        <th>名称</th>
        <th>说明</th>
        <th>使用等级</th>
        <th>品质</th>
        <th>星级</th>
        <th>品级</th>
        <th>类型</th>
        <th>可兑换道具</th>
        <th>是否可用</th>
        <th>Altas路径</th>
        <th>图标</th>
        <th>最大堆叠</th>
        <th>掉落寻路</th>
        <th>出售价格</th>
        <th style="width:60px">操作</th>
    </tr>
</thead>
<tbody>
</tbody>
</table>
<div id="d_attribute" style="float:left;width:60%;"></div>
<div id="d_treasureunlock" style="float:right;width:39%;"></div>
</div>
<div style="height:500px;"></div>
<script type="text/javascript">
clang = {{lang}};
</script>
%rebase content_base js='item'

