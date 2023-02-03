/* Script to automatically toggle all fieldsets with class .collapse.start-open */
'use strict';
{
    window.addEventListener('load', function() {
        var open_toggles = document.querySelectorAll('fieldset.collapse.default-open a.collapse-toggle, fieldset.collapse.start-open a.collapse-toggle');
        for (var i = 0; i < open_toggles.length; i++) {
            open_toggles[i].click();
        }
    });
}
