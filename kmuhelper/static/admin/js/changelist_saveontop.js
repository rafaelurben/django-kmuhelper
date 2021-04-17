'use strict'
var $ = django.jQuery

$(document).ready(function () {
    // Add Buttonrow to top too
    var saveButtonRow = $('.paginator')[0]
    var resultsDiv = $('#changelist-form > div.results')[0]

    if (saveButtonRow && resultsDiv) {
        $(saveButtonRow).clone().insertBefore(resultsDiv);
    }
})