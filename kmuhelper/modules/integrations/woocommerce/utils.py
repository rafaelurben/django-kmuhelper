import base64
import hmac
import hashlib
import secrets
import requests

from kmuhelper import settings


def is_connected() -> bool:
    """Check if WooCommerce has been connected"""

    return bool(settings.get_secret_db_setting("wc-url", False))


def base64_hmac_sha256(key: bytes, message: bytes) -> bytes:
    """Calculate HMAC-SHA256 hash of message using key"""

    return base64.b64encode(hmac.new(key, message, hashlib.sha256).digest())


def random_secret() -> str:
    """Generate a random secret"""

    return secrets.token_urlsafe(32)


def test_wc_url(url: str) -> bool:
    """Test if a URL is a WooCommerce store"""

    try:
        response = requests.get(url.rstrip("/") + "/wp-json/wc/v3")
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return False

    return True
