$(document).ready(function() {
    canui.ajaxSetup();

    // set the container heights
    sizeContent();

    //Helper for looping over JSON objects
    Handlebars.registerHelper("key_value", function(obj, options) {
        var buffer = "",
            key;

        for (key in obj) {
            if (obj.hasOwnProperty(key)) {
                // buffer += function({key: key, value: obj[key]});
                buffer += options.fn({key: key, value:obj[key]});
            }
        }

        return buffer;
    });

    window.loadEndpoint = function loadEndpoint(endpoint_id){
        $.ajax({
            url: "/admin/endpoint_search/?endpoint_id=" + endpoint_id + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                displayResult("endpoint_address", data);
            },
            error: function(data) {
                displayError(data);
            }
        });
    };

    window.loadSubscriptions = function loadSubscriptions(person_id){
        $.ajax({
            url: "/admin/subscription_search/?person_id=" + person_id + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                displayResult("user_subscriptions", data);
            },
            error: function(data) {
                displayError(data);
            }
        });
    };

    window.loadChannel = function loadChannel(channel_id, channel_year, channel_quarter){
        $.ajax({
            url: "/admin/channel_search/?channel_id=" + channel_id + "&channel_year=" + channel_year + "&channel_quarter=" + channel_quarter + "&channel_sln=" + channel_sln + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                displayResult("channel_details_admin", data);
            },
            error: function(data) {
                displayError(data);
            }
        });

    };

    $("#endpoint_by_address").submit(function(elm){
        address = encodeURIComponent($.trim($("#endpoint_address_input").val()));
        $.ajax({
            url: "/admin/endpoint_search/?endpoint_address=" + address + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                displayResult("endpoint_address", data);
            },
            error: function(data) {
                displayError(data);
            }
        });
        return false;
    });

    $("#channel_info").submit(function(elm){
        channel_id = $.trim($("#channel_id").val());
        channel_year = $.trim($("#channel_year").val());
        channel_quarter = $.trim($("#channel_quarter").val());
        channel_sln = $.trim($("#channel_sln").val());
        if(channel_id.length){
            loadChannel(channel_id);
        } else {
            loadChannel(channel_id, channel_year, channel_quarter);
        }

        return false;
    });

    $("#person_info").submit(function(elm){
        regid = $.trim($("#regid").val());
        netid = $.trim($("#netid").val());

        $.ajax({
            url: "/admin/user_search/?regid=" + regid + "&netid=" + netid + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                displayResult("user_details", data);
                if(data.Attributes.SubscriptionCount > 0){
                    contents = $("#SubscriptionCount").html();
                }
            },
            error: function(data) {
                displayError(data);
            }
        });
        return false;
    });

    $("#subscription_info").submit(function(elm){
        person_id = $.trim($("#sub_regid").val()) + "@washington.edu";
        loadSubscriptions(person_id);
        return false;
    });

    function displayResult(template, data){
        template_source = $("#" + template).html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        $("#results").html(html_output);
        //Clear search fields after displaying results, CAN-1045
        $("input").each(function() {
            $(this).val("");
        });
    }

    function displayError(data){
        displayResult("admin_error", JSON.parse(data.responseText));
    }

    window.confirmDelete = function confirmDelete(endpoint_id){
        var confirmed = window.confirm("Are you sure you want to delete this endpoint?");

        if(confirmed){
            $.ajax({
                url: "/admin/endpoint_search/?endpoint_id=" + endpoint_id + "&_=" + jQuery.now(),
                dataType: "json",
                type: "DELETE",
                accepts: {json: "application/json"},
                success: function(data) {
                    $("#results").html("Endpoint deleted");
                },
                error: function(data) {
                    displayError(data);
                }
            });
        }
    };

    getCookie = function getCookie(name) {
        var cookieValue,
            cookies,
            cookie,
            i;
        if (document.cookie && document.cookie !== '') {
            cookies = document.cookie.split(';');
            for (i = 0; i < cookies.length; i++) {
                cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
});

//Every resize of window
$(window).resize(sizeContent);

//Dynamically assign height
function sizeContent() {

     var windowH = $(window).height();
     var contentH = $('#main').height();
     var sideH = $('#side-wrapper').height() + $('#meta-wrapper').height();

     if (contentH < windowH) {
         //$('#main-wrapper').height(windowH);
         $('#main-wrapper').css({'min-height' : sideH});
     }
     else {
         $('#main-wrapper').height("auto");
     }


}
