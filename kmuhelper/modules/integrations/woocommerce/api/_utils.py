from django.utils.html import strip_tags


def preparestring(string):
    """Prepare a HTML string for import"""
    return (
        strip_tags(string.replace("</p>", " ").replace("</strong>", " "))
        .replace("&#8211;", "-")
        .replace("&#8211;", " ")
        .replace("&#215;", "x")
        .replace("&#8220;", '"')
        .replace("&#8221;", '"')
        .replace("&nbsp;", " ")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#8222;", '"')
        .replace("  ", " ")
    )
