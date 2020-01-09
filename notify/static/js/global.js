(function(canuiu, $, undefined){

    Handlebars.registerHelper("if_mobile", function(options) {
        return (is_mobile) ? options.fn(this) : options.inverse(this);
    });

    Handlebars.registerHelper("if_reg_periods", function(options) {
        return (reg_periods.length > 0) ? options.fn(this) : options.inverse(this);
    });

    canui.ACCORDION_OPTIONS = {
        //autoHeight: false,
        heightStyle: "content",
        collapsible: true,
        animate: 400 // miliseconds
    };

    canui.MSG_INVALID_SLN = 'Invalid SLN. SLN must be five digits.';

    canui.ajaxSetup = function ajaxSetup() {
        // prep for api post/put
        $.ajaxSetup({
            headers: { "X-CSRFToken": $('input[name="csrfmiddlewaretoken"]').val() }
        });
    };

    canui.loadSubscriptions = function loadSubscriptions() {
        $.ajax({
            url: "/uiapi/subscription?subscriber_id=" + can_user + "&_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
                if(data.TotalCount > 0){
                    canui.populateSubscriptionList(data);
                }else if(data.TotalCount === 0){
                    $("#subscriptions_loading").remove();
                }
            },
            error: function(data) {
                //handle error
            }
        });
    };

    canui.notificationProtocolButtonClickHandler = function notificationProtocolButtonClickHandler(event) {
      var $btn,
          channel_id,
          enabled,
          method,
          btn_disabled,
          protocol;

      $btn = $(event.target);
      btn_disabled = $btn.prop('disabled');
      if (btn_disabled && btn_disabled === 'disabled') {
          return false;
      }
      enabled = !$btn.hasClass('selected');
      protocol = $btn.hasClass('sms') ? 'SMS' : 'Email';
      method = (enabled === true) ? 'PUT' : 'DELETE';
      $btn.prop('disabled', 'disabled');

      channel_id = $btn.closest('li').first().prop('id');
      subscription = {ChannelID: channel_id, Protocol: protocol, Enabled: enabled};
      if (method === 'DELETE') {
          subscription.EndpointID = $btn.prop('id');
      }
      $.ajax({
          url: "/uiapi/subscription_protocol" + "?_=" + jQuery.now(),
          dataType: "json",
          type: method,
          accepts: {json: "application/json"},
          data: JSON.stringify(subscription),
          success: function(data, textStatus, jqXHR) {
            switch(jqXHR.status) {
              case 304: // notmodified
                  break;
              default:
                  $btn.toggleClass('selected');
                  break;
            }
            $btn.removeProp('disabled');
          },
          error: function(data) {
              $btn.removeProp('disabled');
          }
      });
      return false;
    };

    canui.toggleEndpointButtonStyle = function toggleEndpointButtonStyle($li, fn, class_name) {
        $li.find('span.button_container').first()[fn](class_name)
           .find('button')[fn](class_name);
    };

    // click handler for protocol labels in subscription list
    canui.protocolLabelClickHandler = function protocolLabelClickHandler(event) {
        var protocol_checkbox,
        $label = $(event.target);
        if ($label.prop("tagName") === "INPUT"){
            $label = $label.parent();
        }
        protocol_checkbox = $label.find('input[type="checkbox"]');
        event.preventDefault();
        if (protocol_checkbox && protocol_checkbox.prop('disabled')) {
            // user doesn't have protocol endpoint
            return false;
        }
        is_selected = $label.hasClass('selected');
        $label.toggleClass('selected');
        protocol_checkbox.prop('checked', !is_selected);

    };

    // handler for buttons on the subscription list page
    canui.endpointsButtonClickHandler = function endpointsButtonClickHandler(event) {
        var $btn = $(event.target).first(),
            $li = $btn.closest('li').first(),
            action_class_details,
            action_edit_endpoints
        ;
        parent_li = $btn.parents("li");
        if ($btn.html().match(/Done/i)) {
            event.preventDefault();
            canui.updateChannelSubscriptionsByProtocol($li);
            $li.toggleClass('edit');
            $li.find('div.class_details_container').first().show();
            $li.find('div.edit_endpoints_container').first().hide();
            //Sets focus for keyboard users
            edit_button = $(parent_li).find(".class_details_container > .button_container > .btn");
            edit_button.focus();
        } else {
            $li.toggleClass('edit');
            $li.find('div.class_details_container').first().hide();
            $li.find('div.edit_endpoints_container').first().show();
            //Sets focus for keyboard users
            done_button = $(parent_li).find(".edit_endpoints_container > span > .button_container > .flat");
            done_button.focus();
        }

    };

    canui.channelBySLN = function channelBySLN() {
        var sln,
        $divresults;

        sln = $.trim($('#sln_search').val());
        $divresults = $('div.results');
        reg_period = reg_periods[$("#quarter_selector").val()];

        if(canui.validateSLN(sln)){
            canui.channelSearch(sln, reg_period.year, reg_period.quarter.toLowerCase());
        } else {
            $('#sln_search').addClass('invalid');
            $('#class_details_container').html('<strong>'+canui.MSG_INVALID_SLN+'</strong>');
        }
    };

    canui.channelSearch = function channelSearch(sln, year, quarter) {
            var params = "sln=" + sln + "&year=" + year + "&quarter=" + quarter;
            $.ajax({
                url: "/uiapi/channel_search?" + params + "&_=" + jQuery.now(),
                dataType: "json",
                type: "GET",
                accepts: {json: "application/json"},
                success: function(data) {
                    //Success
                    canui.populateSubscriptionForm(data);

                },
                error: function(data) {
                    //handle error
                    var response = JSON.parse(data.responseText),
                    msg = "<strong>"+response.message+"</strong>";
                    $('#class_details_container').html(msg);
                }
            });
    };

    canui.getCookie = function getCookie(name) {
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

    canui.setCookie = function setCookie(name, value, expire_days) {
        var cookie_value,
            expires_date = new Date();
        expires_date.setDate(expires_date.getDate() + expire_days);
        cookie_value=escape(value) + ((expire_days === null) ? "" : "; expires="+expires_date.toUTCString()+"; path=/");
        document.cookie=name + "=" + cookie_value;
    };


    canui.loadClassDetails = function loadClassDetails(channel_id) {
        $.ajax({
            url: "/uiapi/channel_details/" + channel_id + "?_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            success: function(data) {
               canui.populateClassDetails(data);
            },
            error: function(data) {
                //handle error
            }
        });
    };

    canui.loadProfile = function loadProfile(success_callback) {
        $.ajax({
            url: "/uiapi/profile?_=" + jQuery.now(),
            dataType: "json",
            type: "GET",
            accepts: {json: "application/json"},
            settings: {cache: false},
            success: function(data) {
                has_endpoints.sms = data.hasOwnProperty('sms');
                has_endpoints.email = data.hasOwnProperty('email');
                if (success_callback && typeof(success_callback) === 'function') {
                    success_callback(data);
                } else {
                    canui.populateProfile(data);
                }
            },
            error: function(data) {
                //handle error
            }
        });
    };

    canui.updateEndpoint = function updateEndpoint(data, protocol) {
        var span = $("#" + protocol + "_text > span").first();
        endpoint_delete = $("#" + protocol + "_form > a.remove").first();
        if(!data.hasOwnProperty(protocol)){
            span.html("none saved");
            endpoint_id = $("#" + protocol + "_form > input:hidden");
            endpoint_id.val("");
            endpoint_delete.hide();
            $("#" + protocol + "_input").val("");
        }else{
            span.html(data[protocol].EndpointAddress);
            endpoint_id = $("#" + protocol + "_form>input")[0];
            $(endpoint_id).val(data[protocol].EndpointID);
            endpoint_delete.show();
        }
        if(is_mobile && canui.hasEndpoints()){
            canui.enableProfileNavigation();
        }
        $("#" + protocol + "_form").removeClass('invalid');
        canui.abortEditEndpoint(protocol);
        if(!canui.hasEndpoints()){
            $("#profile_done").addClass('disabled');
        }else{
            $("#profile_done").removeClass('disabled');
        }
        canui.showProfileValidity(data);
    };

    canui.submitEndpoint = function submitEndpoint(request_body, request_type){
        $.ajax({
            url: "/uiapi/profile?_=" + jQuery.now(),
            contentType: "application/json",
            dataType: "json",
            type: request_type,
            data: JSON.stringify(request_body),
            accepts: {json: "application/json"},
            success: function(data) {
                protocol = request_body.Protocol.toLowerCase();
                //Remove unconfirmed messaging
                if(request_type === 'DELETE'){
                    $('div.confirmation_message').hide();
                    $('div.info_endpoint').hide();
                    // at least one endpoint required, hide other delete button
                    $('a.remove').hide();
                }else{
                    //Set 'current_[sms|email]_endpoint' field with new endpoint
                    $("#current_"+ protocol +"_endpoint").val(request_body.EndpointAddress);
                }
                canui.loadProfile(function(data) {
                    canui.updateEndpoint(data, protocol);
                    canui.populateProfileBox(data);
                    $("#endpoint_required").hide();
                });
            },
            statusCode: {
                403: function(data) {
                    response = $.parseJSON(data.responseText);
                    protocol = response.Endpoint.Protocol.toLowerCase();
                    address = response.Endpoint.EndpointAddress;
                    $("#" + protocol + "_form").addClass('invalid');
                    $($("#" + protocol + "_form .error_text")[0]).html(address + " has been attributed to another account. Contact the support team if you believe this is a mistake.");
                }
            }
        });
    };

    canui.requireProfileSetup = function requireProfileSetup(){
        if(canui.hasEndpoints()){
            $.ajax({
                url: "/uiapi/profile?_=" + jQuery.now(),
                dataType: "json",
                type: "GET",
                accepts: {json: "application/json"},
                success: function(data) {
                    canui.populateProfileBox(data);
                },
                error: function(data) {
                    //handle error
                }
            });
            return true;
        }else{
            canui.profileRedirect();
            return false;
        }
    };

    canui.unsubscribeButtonClickHandler = function unsubscribeButtonClickHandler(event) {
        var $btn,
            channel_id = $('input#channel_id').val(),
            params = {ChannelID: channel_id};
        $btn = $(event.target);
        btn_disabled = $btn.prop('disabled');
        if (btn_disabled && btn_disabled === 'disabled') {
            return false;
        }
        $.ajax({
            url: "/uiapi/unsubscribe/" + "?_=" + jQuery.now(),
            contentType: "application/json",
            dataType: "json",
            type: "POST",
            data: JSON.stringify(params),
              accepts: {json: "application/json"},
              success: function(data) {
                  $btn.removeProp('disabled');
                  return canui.postUnsubscribe(channel_id);
              },
              error: function(data) {
                  // display error message?
                  $btn.removeProp('disabled');
                  return false;
              }
        });
        return false;
    };

    canui.unsubscribe_button_active = true;
    canui.loadUnsubscribe = function loadUnsubscribe(channel_id){
        //Disables button during AJAX to prevent multiple popups
        if(canui.unsubscribe_button_active){
            canui.unsubscribe_button_active = false;
            $.ajax({
                url: "/uiapi/channel_details/" + channel_id + "?_=" + jQuery.now(),
                dataType: "json",
                type: "GET",
                accepts: {json: "application/json"},
                success: function(data) {
                    canui.populateUnsubscribe(data);
                    canui.unsubscribe_button_active = true;
                },
                error: function(data) {
                    //handle error
                }
            });
        }
    };

    canui.subscribeBySLN = function subscribeBySLN(event, $form) {
        event.preventDefault();

        var params = $form.serialize();
        if (!params.match(/protocol/)) {
            // no endpoint protocols checked
            return canui.goHome();
        }

        $.ajax({
            url: '/subscribe/' + "?_=" + jQuery.now(),
            type: "POST",
            data: params,
            success: function(data) {
                return canui.goHome();
            },
           statusCode: {
                403: function(data) {
                    message = $.parseJSON(data.responseText).message;
                    canui.resetSubscriptionDialog(message);
                }
            }
        });
    };

    canui.goHome = function goHome() {
        window.location = '/';
    };

    canui.validateEmail = function validateEmail(email_address){
        var re_email = /^[a-z0-9][\w\-\+\.\']*\@([a-z0-9][a-z0-9\-]*\.)+[a-z]+$/i;
        return re_email.test(email_address);
    };

    canui.validatePhone = function validatePhone(phone){
        //strip ONLY US country code
        phone = phone.replace("+1", '');
        phone = phone.replace(/[^0-9]/g, '');
        if(phone.length === 10){
            return true;
        }
        return false;
    };

    canui.validateSLN = function validateSLN(sln){
        var re_sln = /^[0-9]{5,5}$/;
        return re_sln.test(sln);
    };

    canui.bindSelectAllInputText = function bindSelectAllInputText(input_selector) {
        return $(input_selector).focus(function() {
            var $el = $(this);
            $el.select().mouseup(function(e) {
                e.preventDefault();
                $el.unbind(e.type);
            });
        });
    };

    canui.populateProfile = function populateProfile(data){
        var phone_number,
            email_address,
            endpoint_json,
            endpoints = [];
        canui.populateEndpoint(data);

        if(!canui.hasEndpoints()){
            canui.editEndpoint('email', data.DefaultEndpoint.EndpointAddress);
            if(is_mobile){
                 canui.disableProfileNavigation();
            }
        }
        $("#sms_edit").click(function() {
            canui.editEndpoint('sms');
            $("#sms_input").select();
        });
        $("#sms_form>a.remove").click(function() {
            canui.deleteEndpoint('sms');
        });
        $("#email_edit").click(function() {
            canui.editEndpoint('email');
            $("#email_input").select();
        });

       $("#email_form>a.remove").click(function() {
            canui.deleteEndpoint('email');
        });

        $("#sms_form").submit(function(elm) {
            elm.preventDefault();
            if(canui.isEndpointModified('sms')){
                canui.abortEditEndpoint('sms');
            }else{
                endpoint_json = canui.prepareEndpointJSON('sms');
            }

        });
        $("#email_form").submit(function(elm) {
            elm.preventDefault();
            if(canui.isEndpointModified('email')){
                canui.abortEditEndpoint('email');
            }else{
                endpoint_json = canui.prepareEndpointJSON('email');
            }
        });

        $("#profile_done").click(function() {
            if(! $("#profile_done").hasClass('disabled')){
                canui.checkForToSRedirect(canui.closeProfile);
            }
        });

        canui.bindSelectAllInputText("#sms_input");
        canui.bindSelectAllInputText("#email_input");

        $("#sms_resend").click(function(event) {
            var resend_link = $(this);
            if (resend_link.hasClass('disabled')) {
                return false;
            }
            resend_link.addClass('disabled');
            canui.resendSMSConfirmation(event, function(data) {
                resend_link.removeClass('disabled');
                resend_link.parent().hide();
            });
        });
        canui.showProfileValidity(data);
    };

    canui.isEndpointModified = function isEndpointModified(protocol){
        new_endpoint = $("#"+ protocol +"_input").val();
        new_endpoint = $.trim(new_endpoint);
        new_endpoint = new_endpoint.toLowerCase();

        old_endpoint = $("#current_"+ protocol +"_endpoint").val();
        old_endpoint = old_endpoint.toLowerCase();
        return (old_endpoint === new_endpoint);
    };

    canui.showProfileValidity = function showProfileValidity(data){
        sms_status = $("#phone_header").find('.info_endpoint')[0];
        //Reset validity status
        $(sms_status).removeClass('invalid');
        $(sms_status).text('');
        if(data.hasOwnProperty('sms')){
            if(data.sms.isValid){
                if (data.sms.isBlacklisted) {
                    $(sms_status).text('Blacklisted');
                } else if (!data.sms.isConfirmed){
                    $(sms_status).text('Unconfirmed');
                }
            }else{
                $(sms_status).text('Invalid');
                $(sms_status).addClass('invalid');
            }
        }else{

             $(sms_status).removeClass('invalid');
        }
    };


    canui.runCallback = function runCallback(callback, data) {
        if (callback && typeof(callback) === 'function') {
            return callback(data);
        }
        return false;
    };

    canui.resendSMSConfirmation = function resendSMSConfirmation(event, completion_callback) {
        $.ajax({
            url: "/uiapi/resend_sms_confirmation/"  + "?_=" + jQuery.now(),
            type: "POST",
            success: function(data) {
                return true;
            },
            error: function(data) {
                return false;
            },
            complete: function(data) {
                canui.runCallback(completion_callback, data);
            }
        });
    };


    canui.editEndpoint = function editEndpoint(protocol, default_value){
        $("#" + protocol + "_text").hide();
        $("#" + protocol + "_form").show();
        sms = $("#sms_text").find("span")[0];
        email = $("#email_text").find("span")[0];
        if ($("input#email_input").val() && $("input#sms_input").val()) {
            $("#" + protocol + "_form>a.remove").show();
        }
        if(typeof default_value !== 'undefined'){
            $("#email_input").val(default_value);
        }
        if(protocol === 'sms'){
            $("#sms_input").bind('blur keyup',function(e) {
                // handlde blur or Enter key
                if (e.type == 'blur' || e.keyCode == '13')  {
                    phone = $("#sms_input").val();
                    if(canui.validatePhone(phone)){
                        $("#sms_form").removeClass('invalid');
                       $($("#sms_form .error_text")[0]).html('');
                    }else{
                        $("#sms_form").addClass('invalid');
                        $($("#sms_form .error_text")[0]).html('Not a valid U.S. phone #');
                    }
                }
            });
        }
        else{
            $("#email_input").bind('blur keyup',function(e) {
                // handlde blur or Enter key
                if (e.type == 'blur' || e.keyCode == '13') {
                    email = $("#email_input").val();
                    if(canui.validateEmail(email)){
                        $("#email_form").removeClass('invalid');
                        $($("#email_form .error_text")[0]).html('');
                    }else{
                        $("#email_form").addClass('invalid');
                        $($("#email_form .error_text")[0]).html('Not a valid email format');
                    }
                }
            });
        }
    };

    canui.deleteEndpoint = function deleteEndpoint(protocol){
        var endpoint_id,
            form_inputs;
        form_inputs = $("#" + protocol + "_form").find("input");
        endpoint_id = $(form_inputs[0]).val();
        request_body = {"EndpointID": endpoint_id, "Protocol": protocol};
        canui.submitEndpoint(request_body, 'DELETE');
    };

    canui.formatSMSEndpoint = function formatSMSEndpoint(sms){
        var area_code,
            exchange,
            number,
            formatted_sms;

        //strip US country code if provided
        sms = sms.replace(/^\+1/, '');
        //strip punctuation
        sms = sms.replace(/\D/g, '');
        if(sms.length === 10){
            area_code = sms.substring(0,3);
            exchange = sms.substring(3,6);
            number = sms.substring(6,10);
            formatted_sms = area_code + "-" + exchange + "-" + number;
        }
        return formatted_sms;
    };

    canui.prepareEndpointJSON = function prepareEndpointJSON(protocol){
        var endpoint,
            endpoint_id,
            request_type,
            request_body,
            form,
            is_valid = false;
        form = $("#" + protocol + "_form");
        form_inputs = form.find("input");
        endpoint_id = $(form_inputs[0]).val();
        endpoint = $("#"+ protocol +"_input").val();
        endpoint = $.trim(endpoint);
        if(endpoint.length > 0){
            if (protocol === 'sms') {
                protocol = 'SMS';
                if(canui.validatePhone(endpoint)){
                    endpoint = canui.formatSMSEndpoint(endpoint);
                    is_valid = true;
                }else{
                    is_valid = false;
                }

            } else if (protocol === 'email') {
                protocol = 'Email';
                endpoint = endpoint.toLowerCase();
                if(canui.validateEmail(endpoint)){
                    is_valid = true;
                }
            }
            request_body = {"SubscriberID": can_user, "EndpointAddress": endpoint, "Protocol": protocol};
            if(endpoint_id.length > 0){
                request_type = "PUT";
                request_body.EndpointID = endpoint_id;
            } else{
                request_type = "POST";
            }
            if(is_valid){
                canui.submitEndpoint(request_body, request_type);
            } else {
                form.addClass("invalid");
            }

        }
    };

    canui.abortEditEndpoint = function abortEditEndpoint(protocol){
        $("#" + protocol + "_text").show();
        $("#" + protocol + "_form").hide();
        //Clear endpoint errors if we don't save an endpoint
        $("#" + protocol + "_form").removeClass('invalid');
        $($("#" + protocol + "_form .error_text")[0]).html('');
    };

    canui.populateProfileBox = function populateProfileBox(data) {
        var template_source,
            template,
            user_id = can_user,
            match_user_id,
            re_user_id = /^([^@]+)(?:@?)/i,
            html_output;
        template_source = $('#tpl-profile-box').html();
        template = Handlebars.compile(template_source);
        if (match_user_id === user_id.match(re_user_id)) {
            user_id = match_user_id[1];
        }
        data.user_id = user_id;
        html_output = $(template(data));
        $("a.profile").html(html_output);
    };

    canui.registerHandlebarHelpers = function registerHandlebarHelpers() {
        Handlebars.registerHelper('both', function(v1, v2, options) {
            if(v1 === true && v2 === true) {
                return options.fn(this);
            }
            return options.inverse(this);
        });
    };

    canui.endpoint_btn_text_by_protocol = {
        "email": "Email",
        "sms": "SMS"
    };

    // all emails are considered active
    // sms endpoints are active if verified and active === true
    canui._isActiveEndpointCache = {};
    canui.isActiveEndpoint = function isActiveEndpoint(protocol) {
        if (protocol in canui._isActiveEndpointCache) {
            return canui._isActiveEndpointCache[protocol];
        }
        var sms_endpoint = canui.Endpoints.sms, is_active;
        is_active = (protocol === 'email' || (sms_endpoint &&
            sms_endpoint.Status === 'verified' &&
            sms_endpoint.Active === true));
        canui._isActiveEndpointCache[protocol] = is_active;
        return is_active;
    };

    canui.populateSubscriptionList = function populateSubscriptionList(data) {
        var subs_list,
            template_source,
            template,
            channel_id,
            protocol,
            btn_text,
            endpoint_sms,
            endpoints_by_channel = {},
            channel_has_active_endpoint_subscribed,
            html_output,
            checkbox,
            accordion_options,
            registration_period,
            registration_total,
            registration_count,
            registration_period_names = [];
        template_source = $('#tpl-subscription-list').html();
        template = Handlebars.compile(template_source);
        html_output = $(template(data));
        subs_list = $('div.content-container').first();
        canui.Endpoints = data.Endpoints;
        $.each(data.Subscriptions, function(key, subscription) {
            protocol = subscription.Subscription.Endpoint.Protocol.toLowerCase();
            channel_id = subscription.Subscription.Channel.ChannelID;
            if (!endpoints_by_channel.hasOwnProperty(channel_id)) {
                endpoints_by_channel[channel_id] = {};
            }
            endpoints_by_channel[channel_id][protocol] = canui.endpoint_btn_text_by_protocol[protocol];
        });
        checkbox = html_output.find("label.checkbox");
        checkbox.on('click', function(e){
            canui.protocolLabelClickHandler(e);
        });
        html_output.find("button").on('click', canui.endpointsButtonClickHandler);
        // sets button text to subscribed endpoints, checks boxes, and
        // styles span containing button
        html_output.find("li").each(function(key, li) {
            li = $(li);
            btn_text = [];
            channel_id = li.prop('id');
            channel_has_active_endpoint_subscribed = false;
            for (var protocol in endpoints_by_channel[channel_id]) {
                btn_text.push(endpoints_by_channel[channel_id][protocol]);
                li.find('label.'+protocol).addClass('selected');
                var checkbox = li.find('input[type="checkbox"][value="'+protocol+'"]').prop('checked', 'checked');
                // if notification will be sent to endpoint
                // style span containing button accordingly
                if (canui.isActiveEndpoint(protocol)) {
                    if (!channel_has_active_endpoint_subscribed) {
                        canui.toggleEndpointButtonStyle(li, 'addClass', 'active');
                        channel_has_active_endpoint_subscribed = true;
                    }
                }
            }
            //Sort endpoints for button
            btn_text = btn_text.sort(canui.sortEndpointsButtonText);
            li.find("button.btn").html(btn_text.join('<br/>& '));
        });

        //Events for unsubscribe/details links
        html_output.find("li").each(function(index) {
            var $list_element = $(this);
            return (function ($li) {
                var channel_id = $li.attr('id');
                unsubscribe_button = $li.find("span.unsubscribe > a");
                unsubscribe_button.click(function () {
                    canui.openUnsubscribe(channel_id);
                });
                details_button = $li.find("span.class_details > a");
                details_button.click(function () {
                    canui.openClassDetails(channel_id);
                });
              }
            )($list_element);
        });
        subs_list.html(html_output);
        // disable checkboxes for non-existent endpoints
        $.each(data.MissingEndpoints, function(key, protocol) {
            subs_list.find('input[type="checkbox"][value="'+protocol+'"]')
                     .prop('disabled', 'disabled');
            subs_list.find('label.'+protocol).addClass('disabled')
                     .prop('title', 'Edit your profile to enable '+protocol);
        });

        accordion_options = {};
        //accordion_options.autoHeight = canui.ACCORDION_OPTIONS.autoHeight;
        accordion_options.collapsible = canui.ACCORDION_OPTIONS.collapsible;
        accordion_options.heightStyle = canui.ACCORDION_OPTIONS.heightStyle;
        accordion_options.animate = canui.ACCORDION_OPTIONS.animate;

        registration_total = data.RegistrationPeriods.length;
        current_expanded_term = canui.getCookie('expanded_term');
        for (registration_count = 0; registration_count < registration_total; registration_count++) {
            registration_period = data.RegistrationPeriods[registration_count];

            registration_period_names.push(registration_period.RegistrationPeriod);
            if (registration_period.RegistrationPeriod === current_expanded_term) {
                accordion_options.active = registration_count;
            }
        }


        $('.accordion').accordion(accordion_options);
        $('.accordion').bind('accordionchange', function(ev, ui) {
            var index = $('.accordion').accordion( "option", "active");
            if (index === false) {
                canui.setCookie('expanded_term', '', 365);
            }
            else {
                canui.setCookie('expanded_term', registration_period_names[index], 365);
            }
        });
    };

    canui.showSubscriptionForm = function showSubscriptionForm(data){
        var src,
            form,
            template,
            checkbox,
            label,
            not_subscribed = true,
            default_endpoint,
            protocol,
            focus_set = false;
        src = $('#tpl-subscription-form').html();
        template = Handlebars.compile(src);
        $('#create_subscription_container').html(template(data));
        form = $('form[name="form-subscribe"]');
        form.find('label.checkbox').each(function(index) {
            label = $(this);
            checkbox = label.find('input[type="checkbox"]');
            protocol = checkbox.val();
            if(!has_endpoints[protocol]){
                checkbox.prop('disabled', true);
                label.addClass('disabled');
            }else if (has_endpoints[protocol]){
                if(!focus_set && !checkbox.prop('checked')){
                    checkbox.focus();
                }
            }
            if (checkbox.prop('checked')) {
                // don't allow unsubscription from this dialog
                label.addClass('selected');
                not_subscribed = false;
            } else if (!checkbox.prop('disabled')) {

                //For mouse click, toggle label class
                label.on('click', function(event) {
                    label = $(event.target);
                    checkbox = label.find('input[type="checkbox"]');
                    label.toggleClass('selected');
                    checkbox.prop('checked', function(index, wasChecked) {
                        return !wasChecked;
                    });
                    return false;
                });

                //For keyboard press (on input) toggle label class
                checkbox.on('click', function(event) {
                    label = $(event.target).parent();
                    checkbox = $(event.target);
                    label.toggleClass('selected');
                    checkbox.prop('checked', function(index, wasChecked) {
                        return !wasChecked;
                    });
                    return false;
                });
            }
        });

        //If nothing is focused, focus on done btn
        if(!focus_set){
            $("#subscription_submit").focus();
        }
        // if user is not subscribed, pre-select their email or sms endpoint
        if (not_subscribed) {
            if (has_endpoints.email) {
                default_endpoint = 'email';
            } else if (has_endpoints.sms) {
                default_endpoint = 'sms';
            }
            if (default_endpoint) {
                checkbox = form.find('input[type="checkbox"][value="'+default_endpoint+'"]');
                if (checkbox) {
                    checkbox.prop('checked', true);
                    checkbox.closest('label').first().addClass('selected');
                }
            }
        }

        form.submit(function(event) {
            return canui.subscribeBySLN(event, $(this));
        });
    };

    canui.updateChannelSubscriptionsByProtocol = function updateChannelSubscriptionsByProtocol($li) {
        var $form = $li.find('form').first(),
            channel_id = $li.prop('id'),
            params = "channel_id=" + channel_id,
            btn_text = [],
            protocol,
            class_fn,
            idx,
            has_subscriptions = false;

        $form.find('label').each(function(idx, label){
           if($(label).hasClass('selected')){
                has_subscriptions = true;
                params += "&protocol=" + $(label).find('input').first().val();
           }
        });

        if (!has_subscriptions) {
            canui.openUnsubscribe(channel_id);
            return;
        }

        $.ajax({
            url: "/uiapi/subscription_protocol"  + "?_=" + jQuery.now(),
            type: "POST",
            data: params,
            success: function(data) {
                if (data.subscribed_protocols) {
                    if (data.subscribed_protocols.length > 0) {
                        for (idx in data.subscribed_protocols) {
                            if (data.subscribed_protocols.hasOwnProperty(idx)) {
                                protocol = data.subscribed_protocols[idx];
                                btn_text.push(canui.endpoint_btn_text_by_protocol[protocol]);
                            }
                        }
                        btn_text.sort(canui.sortEndpointsButtonText);
                        $li.find("button.btn").html(btn_text.join('<br/>& '));
                        // if subscribed endpoints will get notifications, i.e. are active,
                        // update endpoint span & button style
                        $li.find('input[type="checkbox"]').each(function(key, cb) {
                            var $cb = $(cb);
                            if (canui.isActiveEndpoint($cb.val()) && $cb.prop('checked')) {
                                class_fn = 'addClass';
                                return false;
                            }
                        });
                    } else {
                        $li.hide();
                    }
                }
                if (!class_fn) { class_fn = 'removeClass'; }
                canui.toggleEndpointButtonStyle($li, class_fn, 'active');
                return true;
            },
            error: function(data) {
                return false;
            }
        });
    };

    canui.buildRegistrationPeriodDropdown = function buildRegistrationPeriodDropdown() {
        var idx,
            period,
            selected_index,
            select_box,
            period_list ="";

        selected_index = canui.getCurrentRegistrationPeriodIndex(reg_periods);
        for (idx in reg_periods){
            period = reg_periods[idx];
            period_list += "<option value=\"" + idx + "\">" + period.quarter + " " + period.year + "</option>";
        }
        $("#quarter_selector").html(period_list);

        select_box = $("select").selectBoxIt().data("selectBoxIt");
        select_box.selectOption(selected_index);
        $("#quarter_selector").on('change', function(e){
            target_period = reg_periods[e.target.value];
            target_quarter = target_period.quarter + target_period.year;
            canui.setCookie('default_period', target_quarter, 180);
        });
    };

    canui.getCurrentRegistrationPeriodIndex = function getCurrentRegistrationPeriodIndex(reg_periods) {
        var default_period,
            idx,
            period;
        //If only one period, return it
        if(reg_periods.length === 1){
            return 0;
        }
        //Check for default cookie
        default_period = canui.getCookie("default_period");
        if(typeof default_period !== 'undefined'){
            //If default cookie matches an active period return it, otherwise clear cookie
            for (idx in reg_periods){
                period = reg_periods[idx];
                if(period.quarter + period.year === default_period){
                    return parseInt(idx);
                }
            }
            canui.setCookie("default_period", "", -1);
        }
        //If current period is summer, return next
        if(reg_periods[0].quarter === "Summer"){
            return 1;
        }else{
            return 0;
        }
    };

    // shows and hides CSS based placeholders
    canui.initInputPlaceholder = function initInputPlaceholder(input_selector, placeholder_selector) {
        $(input_selector).on('keyup', function() {
            var placeholder_action = 'addClass';
            if (this.value.match(/^\s*$/)) {
                placeholder_action = 'removeClass';
            }
            $(placeholder_selector)[placeholder_action]('visuallyhidden');
        });
    };

    canui.initAddClassNotificationAddButton = function initAddClassNotificationAddButton() {
        var $btn = $('#sln_submit');
        if ($btn.hasClass('initialized')) {
            return false;
        }
        $btn.click(function(event) {
            var disabled = $btn.hasClass('disabled');
            if (disabled && disabled === 'disabled') {
                return false;
            }
            $btn.addClass('disabled');
            $btn.addClass('initialized');
            //remove expired SLN message
            $("#channel_expired_msg").hide();

            event.preventDefault();
            canui.channelBySLN();
        });
    };

    canui.hasEndpoints = function hasEndpoints(){
        if(typeof has_endpoints !== "undefined"){
            return (has_endpoints.sms || has_endpoints.email);
        }

    };

    canui.loadToS = function loadToS(){
        var redirect_path = "/",
            redirect_path_input = $('input#redirect_path');
        if (redirect_path_input && redirect_path_input.length === 1) {
            redirect_path = '/?next=' + redirect_path_input.val();
        }
        $("#terms_agreement").click(function() {
            $.ajax({
                url: "/uiapi/tos?_=" + jQuery.now(),
                contentType: "application/json",
                dataType: "json",
                type: "POST",
                data:"",
                success: function() {
                    window.location.href = redirect_path;
                }
            });
        });
    };

    canui.sortEndpointsButtonText = function sortEndpointsButtonText(a, b) {
        return a.toUpperCase().localeCompare(b.toUpperCase());
    };

    canui.getRedirectPathFromURL = function getRedirectPathFromURL() {
        var href_match = document.location.href.match(/\/\?next=(.*)/);
        if (href_match && href_match.length >= 2)  {
            return href_match[1];
        }
        return false;
    };

    canui.checkForToSRedirect  = function checkForToSRedirect(alternate_callback) {
        var redirect_path = canui.getRedirectPathFromURL();
        if (redirect_path) {
            window.location.href = redirect_path;
        } else {
            return canui.runCallback(alternate_callback);
        }
    };
}(window.canui = window.canui || {}, jQuery));
