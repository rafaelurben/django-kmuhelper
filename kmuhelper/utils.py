import subprocess
import sys

import requests
from django.contrib import messages
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from packaging.version import Version, InvalidVersion

from kmuhelper.constants import URL_FAQ


################


def render_error(request, status: int = 404, message: str = ""):
    """Show the error page"""

    if message:
        messages.error(request, message)

    return render(request, "kmuhelper/error.html", status=status)


################


def python_version():
    return str(sys.version.split(" ")[0])


def _package_versions_pypi(project, testpypi=False, allow_prereleases=False):
    url = (
        "https://"
        + ("test." if testpypi else "")
        + "pypi.org/pypi/"
        + project
        + "/json"
    )
    versions = requests.get(url).json()["releases"].keys()
    versions_safe = []
    for v in versions:
        try:
            vs = Version(v)
            if not allow_prereleases and vs.is_prerelease:
                continue
            versions_safe.append(vs)
        except InvalidVersion:
            continue
    return sorted(versions_safe)


def _package_version_local(package) -> Version:
    cmd = [sys.executable, "-m", "pip", "show", "{}".format(package)]
    ver = str(subprocess.run(cmd, capture_output=True, text=True))
    ver = ver[ver.find("Version:") + 8 :]
    ver = ver[: ver.find("\\n")].replace(" ", "")
    try:
        return Version(ver)
    except InvalidVersion:
        return None


def package_version(package, testpypi=False):
    all_versions = _package_versions_pypi(package, testpypi)
    latest_version = all_versions[-1] if all_versions else None
    current_version = _package_version_local(package)

    if latest_version and current_version:
        uptodate = latest_version <= current_version
    else:
        uptodate = None

    return {
        # "all":      all_versions,
        "latest": str(latest_version),
        "current": str(current_version),
        "uptodate": uptodate,
    }


################


def getfirstindex(data: list, search: list):
    """Get the index of the first occurence of any string from search in data"""
    for s in search:
        if s in data:
            return data.index(s)
    return None


def formatprice(price):
    """Format a float to exactly 2 decimal places"""
    return "{:.2f}".format(float(price))


def runden(price, to=0.05):
    """Round a float to .05 or any other value"""
    # Note: formatprice is used because of floating point approximation
    return float(formatprice(float(round(round(price / to) * to, 2))))


###############


def modulo10rekursiv(strNummer):
    intTabelle = [
        [0, 9, 4, 6, 8, 2, 7, 1, 3, 5],
        [9, 4, 6, 8, 2, 7, 1, 3, 5, 0],
        [4, 6, 8, 2, 7, 1, 3, 5, 0, 9],
        [6, 8, 2, 7, 1, 3, 5, 0, 9, 4],
        [8, 2, 7, 1, 3, 5, 0, 9, 4, 6],
        [2, 7, 1, 3, 5, 0, 9, 4, 6, 8],
        [7, 1, 3, 5, 0, 9, 4, 6, 8, 2],
        [1, 3, 5, 0, 9, 4, 6, 8, 2, 7],
        [3, 5, 0, 9, 4, 6, 8, 2, 7, 1],
        [5, 0, 9, 4, 6, 8, 2, 7, 1, 3],
    ]
    strNummer = strNummer.replace(" ", "")
    uebertrag = 0
    for num in strNummer:
        uebertrag = intTabelle[uebertrag][int(num)]
    return [0, 9, 8, 7, 6, 5, 4, 3, 2, 1][uebertrag]


###############


def faq(anchor="", text=_("FAQ")):
    """Get a link to the FAQ page in the manual."""

    href = f"{URL_FAQ}#{anchor}"
    return format_html('<a target="_blank" href="{}">{}</a>', href, text)
