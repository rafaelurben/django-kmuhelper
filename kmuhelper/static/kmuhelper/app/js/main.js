function loadPage() {
    const frame = document.getElementById("frame");
    const hash = window.location.hash.substr(1);
    const page = document.getElementById(hash || "home");
    if (page) {
        frame.contentDocument.documentElement.innerHTML = ""; // clear current page
        frame.src = page.getAttribute("url");
    } else {
        frame.src = "error";
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
