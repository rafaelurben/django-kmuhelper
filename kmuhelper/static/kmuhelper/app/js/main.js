function loadPage() {
    const frame = document.getElementById("frame");
    const page = window.location.hash.substr(1);
    const pageIDs = ["home","notiz","versand","zahlung"];
    if (pageIDs.includes(page)) {
        frame.src = "";
        setTimeout(function () {
            frame.src = document.getElementById(page).getAttribute("url");
        }, 10);
    } else {
        window.location.hash = "home";
    }
}

window.onhashchange = loadPage;
window.onload = loadPage;
