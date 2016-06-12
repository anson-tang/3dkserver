<div style="overflow-y:scroll;height:800px">
<div class="ui-state-active"><h3><b>登陆</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<form id="frm_login" method="POST" action="/do_login" target="_self" enctype="application/x-www-form-urlencoded">
<fieldset>
    <table border="0">   
    <tr>
        <td>帐号：</td><td><input type="text" id="username" name="username"/></td>
    </tr>
    <tr>
        <td>密码：</td><td><input type="password" id="password" name="password"/></td>
    </tr>
    <tr>
        <td><button id="btn_login" onclick="return login();">登陆</button></td>
    </tr>
    </table>
</fieldset>
</form>
</div>

</div>
      
%rebase content_base js='login'
