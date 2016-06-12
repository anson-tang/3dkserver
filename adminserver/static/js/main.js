function resize() {
    var iframe = $("#content");
    if (iframe) {
        iframe.height(iframe.contents().height());
    }

    $('#autoheight').height($(window).height() * .6);
}

$(function() {
    //$( "#accordion" ).accordion({heightStyle:"content"});
    $( "#accordion" ).accordion({heighStyle:"fill", active:1, collapsible: true});
    $(".mbtn").button();

    resize();

    $(window).resize(resize);

});
