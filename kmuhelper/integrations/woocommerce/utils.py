from kmuhelper import settings


def is_connected():
    """Check if WooCommerce has been connected"""

    return bool(settings.get_secret_db_setting("wc-url", False))
