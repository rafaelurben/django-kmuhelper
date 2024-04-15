/**
 * Helper method that warns a user if they try to leave a page on which the have changed form values.
 */

window.addEventListener("load", function () {
    let $;
    if (typeof django !== 'undefined') {
        $ = django.jQuery;
    } else if (typeof jQuery !== 'undefined') {
        $ = jQuery;
    } else if (typeof $ === 'undefined') {
        console.error("jQuery not found!");
        return;
    }

    window.initialData = "";
    let isSubmitting = false;

    const $form = $('form');
    $form.not("#changelist-search").submit(() => {
        isSubmitting = true;
        console.log("Form submitted...");
    })

    window.initialData = $form.not("#changelist-search").serialize();

    $(window).on('beforeunload', function () {
        console.log("[Beforeunload] - Event triggered!");
        const formDidChange = $('form').not("#changelist-search").serialize() !== window.initialData;
        console.log("[Beforeunload] - Form changed:", formDidChange);
        if (!isSubmitting && formDidChange) {
            console.log("[Beforeunload] - Unload prevented!");
            return 'Du hast ungesicherte Änderungen vorgenommen. Wenn du die Seite verlässt, werden diese gelöscht.'
        }
    });
});