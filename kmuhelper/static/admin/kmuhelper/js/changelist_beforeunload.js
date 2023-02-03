window.addEventListener("load", function () {
    var $ = django.jQuery;

    window.initialData = "";
    var isSubmitting = false;

    $('form').not("#changelist-search").submit(function (event) {
        isSubmitting = true;
        console.log("Form submitted...");
    })

    window.initialData = $('form').not("#changelist-search").serialize();

    $(window).on('beforeunload', function () {
        console.log("[Beforeunload] - Event triggered!");
        var formChanged = $('form').not("#changelist-search").serialize() != window.initialData;
        console.log("[Beforeunload] - Form changed:", formChanged);
        if (!isSubmitting && formChanged) {
            console.log("[Beforeunload] - Unload prevented!");
            return 'Du hast ungesicherte Änderungen vorgenommen. Wenn du die Seite verlässt, werden diese gelöscht.'
        }
    });
});