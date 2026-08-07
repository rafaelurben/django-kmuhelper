/* Script to automatically toggle all fieldsets with class .collapse.start-open */
'use strict';

window.addEventListener('load', function () {
    const collapsers = document.querySelectorAll('fieldset.collapse.start-open summary');
    for (const element of collapsers) {
        element.click();
    }
});
