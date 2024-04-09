from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseAPI


class WCGeneralAPI(WC_BaseAPI):
    """Manage connection with WooCommerce"""

    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce][/] -"

    # System status

    def get_system_status(self):
        """Get system status from WooCommerce"""
        try:
            request = self.wcapi.get("system_status")
            request.raise_for_status()
            return request.json()
        except Exception as e:
            self.log("Error while getting system status: ", e)
            return False
