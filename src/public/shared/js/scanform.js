$(document).ready(function() {
    // hide everything
    $(".options").children().addClass("collapsed");
    
    // check if we need to expand any of our lists, due to errors
    if ($("#hostDiscovery > ul > li > ul").hasClass("errorlist")) {
        $("#hostDiscovery").children().removeClass("collapsed");
    }

    if ($("#scanTechniques > ul > li > ul").hasClass("errorlist")) {
        $("#scanTechniques").children().removeClass("collapsed");
    }
    
    $(".options").toggle(
        function() {
            $(this).children().slideDown("medium");
            $(this).css("background", 
                "url(/images/minus-icon-16x16.png) no-repeat 0 4px");
        },
        function() {
            $(this).children().slideUp("fast");
            $(this).css("background", 
                "url(/images/plus-icon-16x16.png) no-repeat 0 4px");
        });
    // clicks inside the options list shouldn't close the container
    $(".options > ul").click(function(event) {
        event.stopPropagation();
    });
    // disable everything else if Pn selected
    $("#id_Pn").click(function() {
        $("#hostDiscovery > ul > li :not(#id_Pn)").attr("checked", false);
    });
    // uncheck Pn if another sibling is selected
    $("#hostDiscovery > ul > li :not(#id_Pn)").click(function() {
        $("#id_Pn").attr("checked", false);
    });
});