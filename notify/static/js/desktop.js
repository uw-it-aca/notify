(function(canui, $, undefined){
    $(document).ready(function() {
        if (document.location.href.match(/\/tos/)) {
            canui.loadToS();
        } else if (document.location.href.match(/[^=]\/course/)) {
            canui.loadCourseSearch();
        } else {
            if(canui.requireProfileSetup()){
                canui.checkForToSRedirect(canui.loadSubscriptions);
            }
        }

        canui.registerHandlebarHelpers();
    });

    canui.populateEndpoint = function populateEndpoint(endpoint) {
        var template,
            template_source,
            html_output;
            template_source = $('#endpoint').html();
            template = Handlebars.compile(template_source);
            html_output = $(template(endpoint));
            html_output = $('<div class="profile"></div>').append(html_output);
            if(!canui.hasEndpoints()){
                $(html_output).find("#profile_done").addClass('disabled');
            }
            canui.profileDialog = html_output.dialog({"height": 400, "width": 500,
                    "draggable": false, "autoOpen": false, "modal": true,
                    "title": "<h2><span class='visuallyhidden'>Manage </span>Your Profile</h2>", 'beforeClose': function( event, ui ) {return canui.beforeProfileClose();},
                    "close": function(event, ui){$(this).dialog('destroy').remove();}});
            $('input, textarea').placeholder();
            canui.profileDialog.dialog('open');
    };

    canui.openFindDialog = function openFindDialog() {
        if(canui.subscriptionDialog !== undefined){
            canui.resetSubscriptionDialog();
            canui.subscriptionDialog.dialog('open');
        } else{
            template_source = $('#find').html();
            template = Handlebars.compile(template_source);
            html_output = $(template());
            html_output = $('<div></div>').append(html_output);
            canui.subscriptionDialog = html_output.dialog({"height": 460, "width": 600, "draggable": false, "autoOpen": false, "modal": true, "title": "<h2>Add Class Notification</h2>"});
            canui.initInputPlaceholder('#sln_search', '#sln_placeholder');
            canui.subscriptionDialog.dialog('open');
            canui.buildRegistrationPeriodDropdown();
            $('input, textarea').placeholder();
        }
        canui.initAddClassNotificationAddButton();
    };

    canui.resetSubscriptionDialog = function resetSubscriptionDialog(error) {
        var sln_input = $("#sln_search");
        sln_input.val("");
        sln_input.parent().show();
        $("#class_details_container").html("");
        $("#create_subscription_container").html("");
        $("#sln_placeholder").removeClass("visuallyhidden");
        if(error !== undefined){
            sln_input.val(error.sln);
            $("#channel_expired_msg").html("The class with SLN " + error.sln + " is no longer being offered for " + error.quarter + " " + error.year);
            $("#channel_expired_msg").show();
        }
    };

    canui.details_dialog_is_open = false;
    canui.populateClassDetails = function populateClassDetails(data) {
        //Prevent multiple details dialogs from opening
        if(canui.details_dialog_is_open === false){
            canui.details_dialog_is_open = true;
            template_source = $('#class_details').html();
            template = Handlebars.compile(template_source);
            html_output = $(template(data));
            html_output = $('<div></div>').html(html_output);
            canui.classDetailsDialog = html_output.dialog({"height": 400, "width": 600,
                    "draggable": false, "autoOpen": false, "modal": true, "title": "<h2>Class Details</h2>",
                    "close": function(event, ui){
                        $(this).dialog('destroy').remove();
                        canui.details_dialog_is_open = false;
                    }});
            canui.classDetailsDialog.dialog('open');
        }
    };

    canui.populateUnsubscribe = function populateUnsubscribe(data){
        template_source = $('#unsubscribe').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        html_output = $('<div id="find_div"></div>').append(html_output);
        canui.unsubscribeDialog = html_output.dialog({"height": 250, "width": 500,
                "draggable": false, "autoOpen": false, "modal": true, "title": "<h2>Unsubscribe</h2>",
                "close": function(event, ui){$(this).dialog('destroy').remove();}});
        canui.unsubscribeDialog.dialog('open');
        $('#confirm_unsubscribe').on('click', canui.unsubscribeButtonClickHandler);
    };

    canui.populateFindDetails = function populateFindDetails(data) {
        template_source = $('#class_details').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        html_output = $("#class_details_container").html(html_output);

    };

    canui.openClassDetails = function openClassDetails(channel_id){
        canui.loadClassDetails(channel_id);
    };

    canui.openUnsubscribe = function openUnsubscribe(channel_id){
        var course_abbr = $("#"+channel_id+" div.class_details_container span.class_name").text(),
            data = {"course_abbr": course_abbr, "channel_id": channel_id};
        canui.populateUnsubscribe(data);
    };

    canui.postUnsubscribe = function postUnsubscribe(channel_id){
        var $li = $('li#' + channel_id),
            $ol = $li.parent(),
            $div;
        $li.remove();
        if ($ol.find("li").length === 0) {
            $div = $ol.parent();
            $div.prev().remove();
            $div.remove();
        }
        canui.unsubscribeDialog.dialog('close');
    };

    canui.populateSubscriptionForm = function populateSubscriptionForm(data){
        canui.populateFindDetails(data);
        canui.showSubscriptionForm(data);
        $("#sln_search").parent().hide();
    };

    canui.profileRedirect = function profileRedirect(){
        //Hide loading message on first load
        $("#subscriptions_loading").remove();
        canui.loadProfile();
    };

    canui.beforeProfileClose = function beforeProfileClose(){
        if(!canui.hasEndpoints()){
            $("#endpoint_required").show();
            return false;
        }
    };

    canui.closeProfile = function closeProfile(){
        canui.profileDialog.dialog("close");
    };

    canui.loadCourseSearch = function loadCourseSearch() {
        if (sln && year && quarter) {
            canui.openFindDialog();
            canui.channelSearch(sln, year, quarter);
            canui.subscriptionDialog.on("dialogclose", function() {
                return canui.goHome();
            });
        }
    };
}(window.canui = window.canui || {}, jQuery));
