$(document).ready(function() {
    // hide everything
    $(".options").children("ul").addClass("collapsed");
    
    // check if we need to expand any of our lists, due to errors
    if ($("#hostDiscovery > ul > li > ul").hasClass("errorlist")) {
        $("#hostDiscovery").children().removeClass("collapsed");
    }

    if ($("#scanTechniques > ul > li > ul").hasClass("errorlist")) {
        $("#scanTechniques").children().removeClass("collapsed");
    }
    
    $(".options").toggle(
        function() {
            $(this).children("ul").slideDown("medium");
        },
        function() {
            $(this).children("ul").slideUp("fast");
        });
    // clicks inside the options list shouldn't close the container
    $(".options > ul").click(function(event) {
        event.stopPropagation();
    });
    
    // uncheck other hostDiscovery options if -Pn selected
    $("#id_Pn").click(function() {
        $("#hostDiscovery > ul > li :not(#id_Pn)").attr("checked", false);
    });
    // uncheck -Pn if another sibling is selected
    $("#hostDiscovery > ul > li :not(#id_Pn)").click(function() {
        $("#id_Pn").attr("checked", false);
    });
    
    // uncheck scanTechniques if -sn selected
    $("#id_sn").click(function() {
        $("#scanTechniques > ul > li input:checkbox").attr("checked", false);
        $("#scanTechniques > ul > li input:text").val("");
    });
    // uncheck -sn if a scanTechnique is selected
    $("#scanTechniques > ul > li").click(function() {
        $("#id_sn").attr("checked", false);
    })
    
    // enable "mail on errors" if "mail on all" is checked
    $("#id_mra").click(function() {
        $("#id_mre").attr("checked", true);
    });
    // disable "mail on all" if "mail on errors" is unchecked
    $("#id_mre").click(function() {
        $("#id_mra").attr("checked", false);
    });
});