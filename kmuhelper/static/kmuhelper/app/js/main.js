function loadPage() {
    const frame = document.getElementById("frame");
    const hash = window.location.hash.substr(1);
    if (hash) {
        const page = document.getElementById(hash);
        if (page) {
            frame.src = "about:blank";
            setTimeout(function () {
                frame.src = page.getAttribute("url");
            }, 10);
        } else {
            frame.src = "error";
        }
    } else {
        window.location.hash = "home";
    }
}

function checkFrame(frame) {
    if (!frame.contentDocument || !frame.contentDocument.location) {
        window.location.hash = "error";
    }
}

window.onhashchange = loadPage;
window.onload = function () {
    loadPage();
};
