<div style="overflow-y:scroll;height:800px">
<div class="ui-state-active"><h3><b>账号注册</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
      
<fieldset>
    <table border="0">   
    <tr>
        <td>注册入口：</td>   
        <td>
            <select id="server" name="server">
                %for idx, v in enumerate(servers):
                <option value="{{idx+1}}">{{v}}</option>
                %end
            </select>            
        </td>
    </tr>
    <tr>
        <td>用户名 ：</td><td><input type="text" id="username" name="username" /></td>
    </tr>
    <tr>
        <td>密码：</td><td></label><input type="password" id="password" name="password"/></td>
    </tr>
    <tr>
        <td>确认密码：</td><td></label><input type="password" id="ch_password" name="ch_password" onchange="check_passwd();"/><div id="show_msg" ></div></td>
    </tr>
    <tr>
        <td><button id="regist" onclick="return regist();">注册</button></td>
    </tr>
    </table>
</fieldset>
</div>
</div>
      
%rebase content_base js="register"
