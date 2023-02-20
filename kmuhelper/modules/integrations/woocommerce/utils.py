import base64
import hmac
import hashlib

from kmuhelper import settings

def is_connected() -> bool:
    """Check if WooCommerce has been connected"""

    return bool(settings.get_secret_db_setting("wc-url", False))

def base64_hmac_sha256(key: bytes, message: bytes) -> bytes:
    """Calculate HMAC-SHA256 hash of message using key"""

    return base64.b64encode(hmac.new(key, message, hashlib.sha256).digest())
