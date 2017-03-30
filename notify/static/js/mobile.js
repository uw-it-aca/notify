(function(canuiu, $, undefined){
    $(document).ready(function() {
        var href = document.location.href,
            parts;
        if (href.match(/\/find/)) {
            canui.requireProfileSetup();
            canui.populateFindPage();
        } else if (href.match(/\/class_details/)){
            canui.requireProfileSetup();
            parts = href.split("/");
            canui.loadClassDetails(parts.pop());
        } else if (href.match(/\/profile/)){
            canui.loadProfile();
        } else if (href.match(/\/unsubscribe/)){
            canui.requireProfileSetup();
            parts = href.split("/");
            canui.loadUnsubscribe(parts.pop());
        } else if (href.match(/[^=]\/course/)) {
            canui.requireProfileSetup();
            canui.loadCourseSearch();
        } else if (document.location.href.match(/\/tos/)) {
            canui.loadToS();
        } else {
            if(canui.requireProfileSetup()){
                canui.checkForToSRedirect(canui.loadSubscriptions);
            }
        }
        canui.registerHandlebarHelpers();
    });

    canui.populateFindPage = function populateFindPage(){
        template_source = $('#find').html();
        template = Handlebars.compile(template_source);
        html_output = $(template());
        $("div#body").html(html_output);
        canui.initInputPlaceholder('#sln_search', '#sln_placeholder');
        canui.initAddClassNotificationAddButton();
        canui.buildRegistrationPeriodDropdown();
        canui.bindSelectAllInputText('#sln_search').focus();
        $('input, textarea').placeholder();
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

    canui.populateUnsubscribe = function populateUnsubscribe(data){
        template_source = $('#unsubscribe').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        $("div#body").html(html_output);
        $('#confirm_unsubscribe').on('click', canui.unsubscribeButtonClickHandler);
    };

    canui.populateEndpoint = function populateEndpoint(endpoint){
        var template,
            template_source,
            html_output;

        template_source = $('#endpoint').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(endpoint));
        if(!canui.hasEndpoints()){
            $(html_output).find("#profile_done").addClass('disabled');
        }
        $("#profile").html(html_output);
        $('input, textarea').placeholder();
    };

    canui.populateClassDetails = function populateClassDetails(data) {
        var details_container,
            template_source,
            template,
            html_output;
        template_source = $('#class_details').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        details_container = $('#class_details_container');
        details_container.html(html_output);
    };

    canui.openClassDetails = function openClassDetails(channel_id){
        window.location.href = "/class_details/" + channel_id;
    };

    canui.openUnsubscribe = function openUnsubscribe(channel_id){
        window.location.href = "/unsubscribe/" + channel_id;
    };

    canui.postUnsubscribe = function postUnsubscribe(){
        canui.goHome();
    };

    canui.populateSubscriptionForm = function populateSubscriptionForm(data){
        canui.populateClassDetails(data);
        $("#sln_search").parent().hide();
        canui.showSubscriptionForm(data);
    };

    canui.profileRedirect = function profileRedirect(){
        var profile_path = "/profile",
            redirect_path = canui.getRedirectPathFromURL();
        if (redirect_path) {
            profile_path += '?next=' + redirect_path;
        }
        window.location.href = profile_path;
    };

    canui.disableProfileNavigation = function disableProfileNavigation(default_endpoint){
        $("a.back").hide();
    };

    canui.enableProfileNavigation = function enableProfileNavigation(){
        $("a.back").show();
    };

    canui.closeProfile = function closeProfile(){
        if(canui.hasEndpoints()){
            window.location.href = "/";
        }
    };

    canui.loadCourseSearch = function loadCourseSearch() {
        if (sln && year && quarter) {
            canui.channelSearch(sln, year, quarter);
            canui.populateFindPage();
            $('.find_sln_container').hide();
        }
    };
}(window.canui = window.canui || {}, jQuery));

