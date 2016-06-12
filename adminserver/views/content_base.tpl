% import random
% setdefault('v', random.random())
<!DOCTYPE HTML>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
<link href="/static/css/jquery-ui-1.9.2.custom.min.css?v={{v}}" rel="stylesheet" type="text/css">
<link href="/static/css/table.css?v={{v}}" rel="stylesheet" type="text/css">
<link href="/static/css/jquery.dataTables.css?v={{v}}" rel="stylesheet" type="text/css">
<link href="/static/css/main.css?v={{v}}" rel="stylesheet" type="text/css">

<script type="text/javascript" src="/static/js/jquery-1.8.3.js"></script>
<script type="text/javascript" src="/static/js/jquery-ui-1.9.2.custom.min.js"></script>
<script type="text/javascript" src="/static/js/jquery.dataTables.min.js"></script>
<script type="text/javascript" src="/static/js/{{js or 'main'}}.js?v={{v}}"></script>
</head>
<body onload="parent.resize();return false;">  
%include
</body>
</html>

