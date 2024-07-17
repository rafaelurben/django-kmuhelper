/* Script to automatically toggle all fieldsets with class .collapse.start-open */
'use strict';
{
    window.addEventListener('load', function () {
        const collapsers = document.querySelectorAll('fieldset.collapse.start-open :is(summary, .collapse-toggle)');
        // Note: details is for Django>=5.1, .collapse-toggle for Django<5.1
        for (let i = 0; i < collapsers.length; i++) {
            collapsers[i].click();
        }
    });
}
