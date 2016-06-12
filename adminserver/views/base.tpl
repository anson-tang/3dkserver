% import random
% setdefault('v', random.random())
<!DOCTYPE HTML>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
<title>3DK后台数值管理系统</title>
<link rel="icon" href="static/favicon.ico" mce_href="static/favicon.ico" type="image/x-icon">
<link rel="shortcut icon" href="static/favicon.ico" mce_href="static/favicon.ico" type="image/x-icon">                                                                                          
<link href="/static/css/jquery-ui-1.9.2.custom.min.css?v={{v}}" rel="stylesheet" type="text/css">
<link href="/static/css/main.css?v={{v}}" rel="stylesheet" type="text/css">

<script type="text/javascript" src="/static/js/jquery-1.8.3.js"></script>
<script type="text/javascript" src="/static/js/jquery-ui-1.9.2.custom.min.js"></script>
<script type="text/javascript" src="/static/js/main.js?v={{v}}"></script>
</head>
<body>  
<div id="page">
    <div id="header">
        <div id="banner"></div>
    </div>
    <div id="region" nowrap>
        <div id="sidebar">
            %include mainmenu
        </div>
        <div id="main">
            <iframe id="content" style="width:100%;" allowtransparency="yes" border="0" marginwidth="0" marginheight="0"
            scrolling="no" frameborder="0" src="/default"></iframe>
        </div>
    <!--    <div style="clear:both;"></div>
    </div>
    <div class="ui-widget-content">
        <p>
        &copyright;111111111111
        </p>
        -->
    </div>
</div>
</body>
</html>

