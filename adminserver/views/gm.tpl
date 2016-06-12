<div style="overflow-y:scroll;height:800px">
<div class="ui-state-active"><h3><b>GM命令</b></h3></div>
<div style="margin:0px 0px 30px 0px;">
<fieldset>
    <table border="0">   
    <tr>
        <td>命令帮助：</td>   
        <td>
            <select id="cmd_help_list" name="cmd_help_list">
                %for cmd, v in help_dic.iteritems():
                <option value="{{cmd}}">{{v}}</option>
                %end
            </select>
        </td>
    </tr>
    <tr>
        <td>选择服务器:</td>   
        <td>
            <select id="svc" name="svc">
                %for idx, svc in enumerate(svcs):
                <option value="{{idx}}">{{svc[0]}}</option>
                %end
            </select>
        </td>
    </tr>
    <tr>
        <td>说明：</td><td>新增道具-可新增道具数值管理中的任一类型道具, 如: duan1 1 2 888</td>
    </tr>
    <tr>
        <td>命令参数：</td><td><input type="text" id="cmd_args" name="cmd_args"/></td>
    </tr>
    <tr>
        <td><button id="btn_gm_cmd" onclick="return exe_gm_cmd_js();">执行</button></td>
    </tr>
    </table>
</fieldset>
</div>

<div style="margin:0px 0px 30px 0px;">
<fieldset>
    <table border="0">   
    <tr>
        <td>选择服务器:</td>   
        <td>
            <select id="svc1" name="svc1">
                %for idx, svc in enumerate(svcs):
                <option value="{{idx + 1}}">{{svc[0]}}</option>
                %end
            </select>
        </td>
    </tr>
    <tr>
        <td>帐号：</td><td><input type="text" id="account" name="account"/></td>
    </tr>
    <tr>
        <td>充值：</td><td><input type="text" id="change_id" name="change_id"/></td>
    </tr>
    <tr>
        <td><button id="btn_payment" onclick="return payment();">充值</button></td>
    </tr>
    </table>
</fieldset>
</div>

</div>
      
%rebase content_base js="gm"
