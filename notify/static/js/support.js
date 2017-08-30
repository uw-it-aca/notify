/*jslint browser: true, plusplus: true */
/*global $, jQuery, alert */
(function ($) {
    "use strict";

    function person_resource_by_regid() {
        var regid = $.trim($("#person_regid").val());
        if (regid === "") {
            alert("Missing REGID");
        } else {
            window.location.href = window.notify.person_url + "/" + regid;
        }
        return false;
    }

    function person_resource_by_netid() {
        var netid = $.trim($("#person_netid").val());
        if (netid === "") {
            alert("Missing NETID");
        } else {
            window.location.href = window.notify.person_url + "/" +
                netid + "@washington.edu";
        }
        return false;
    }

    function endpoint_resource_by_endpoint_addr() {
        var endpoint_addr = $.trim($("#endpoint_address").val()),
            re = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
        if (endpoint_addr === "") {
            alert("Missing Endpoint Address or ID");
        } else if (re.test(endpoint_addr)) {
            window.location.href = window.notify.endpoint_url + "/" + endpoint_addr;
        } else {
            window.location.href = window.notify.endpoint_url + "?" +
                $.param({endpoint_address: endpoint_addr});
        }
        return false;
    }

    function channel_resource_by_channel_id() {
        var channel_id = $.trim($("#channel_id").val());
        if (channel_id === "") {
            alert("Missing Channel ID");
        } else {
            window.location.href = window.notify.channel_url + "/" + channel_id;
        }
        return false;
    }

    function channel_search_by_sln_year_quarter() {
        var params = {
            type: "uw_student_courseavailable",
            tag_quarter: $("#channel_quarter").val(),
            tag_year: $.trim($("#channel_year").val()),
            tag_sln: $.trim($("#channel_sln").val())
        };
        if (params.tag_year === "") {
            alert("Missing year");
        } else if (params.tag_sln === "") {
            alert("Missing SLN");
        } else {
            window.location.href = window.notify.channel_url + "?" + $.param(params);
        }
        return false;
    }

    function subscription_search_by_netid() {
        var netid = $.trim($("#sub_netid").val());
        if (netid === "") {
            alert("Missing METID");
        } else {
            window.location.href = window.notify.subscription_url + "?" +
                $.param({subscriber_id: netid + "@washington.edu"});
        }
        return false;
    }

    function delete_endpoint() {
        /*jshint validthis: true */
        var endpoint_id = $(this).data("endpoint_id"),
            msg = "Are you sure you want to delete this endpoint?";

        if (window.confirm(msg)) {
            $.ajax({
                url: "/admin/endpoint/" + endpoint_id,
                headers: {
                    "X-CSRFToken": $('input[name="csrfmiddlewaretoken"]').val()
                },
                dataType: "json",
                type: "DELETE",
                accepts: {json: "application/json"},
            }).done(function(data) {
                window.location.href = window.location.href;
            }).fail(function(xhr) {
                alert("Delete failed: " + xhr.status + " " + xhr.statusText);
            });
        }
    }

    function add_endpoint_delete() {
        /*jshint validthis: true */
        var el = $(this).next(),
            endpoint_id = $.trim(el.text()),
            btn = $("<button></button>")
                    .addClass("btn btn-danger btn-sm")
                    .text("Delete endpoint")
                    .data("endpoint_id", endpoint_id)
                    .on("click", delete_endpoint);

        el.append("&nbsp;&nbsp;");
        el.append(btn);
    }

    $(document).ready(function () {
        var url_re = /^\/notification\/v1\//;

        $("#channel-id-form").on("submit", channel_resource_by_channel_id);
        $("#channel-search-form").on("submit", channel_search_by_sln_year_quarter);
        $("#person-regid-form").on("submit", person_resource_by_regid);
        $("#person-netid-form").on("submit", person_resource_by_netid);
        $("#endpoint-addr-form").on("submit", endpoint_resource_by_endpoint_addr);
        $("#subscription-netid-form").on("submit", subscription_search_by_netid);

        if (url_re.test($("#restclients-proxy-url").val())) {
            $("span.json-key:contains('EndpointID :')").each(add_endpoint_delete);
        }
    });
}(jQuery));
