<div class="ui-state-active"><h3><b>多语言明细</b></h3></div>
<fieldset>
<legend>参数列表:</legend>
<form id="frm" method="POST" action="/keyword/save">
<p>
    <label class="flbl" for="inter_key">多语言_键:</label><input name="inter_key" value="{{data[0]}}" type="text"/>
    &nbsp;&nbsp;&nbsp;&nbsp;
    <label class="flbl" for="inter_value">多语言_值:</label><input name="inter_value" value="{{data[1]}}" type="text" />
</p>

<input type="hidden" name="_new" value="{{new}}" />
<input type="hidden" name="lang" value="{{lang}}" />
</form>
</fieldset>
<div style="padding:5px 10px;height:50px;border:0px;" class="ui-widget-header">
<button id="save" onclick="$('#frm').submit();return false;"><span class="ui-icon ui-icon-circle-check"></span>保存</button>
%if not new:
<button id="del" onclick="return keyword_delete({{data[0]}});"> 
%else:
<button id="del" disabled>
%end
<span class="ui-icon ui-icon-power"></span>
删除</button>
<button id="back" onclick="$(location).attr('href', '/keyword');return false;"><span class="ui-icon
ui-icon-home"></span>返回</button> 
</div>
<script type="text/javascript">
c_lang = {{lang}};
</script>
%rebase content_base js='keyword'
