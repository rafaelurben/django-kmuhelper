from requests import HTTPError, JSONDecodeError

from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseAPI


class WCGeneralAPI(WC_BaseAPI):
    """Manage connection with WooCommerce"""

    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce][/] -"

    # System status

    def get_system_status(self):
        """Get system status from WooCommerce"""
        try:
            response = self.wcapi.get("system_status")
            response.raise_for_status()
            return response.json()
        except (HTTPError, JSONDecodeError) as e:
            self.log("Error while getting system status: ", e)
            return False

    def get_enabled_webhooks_topics(self, delivery_url) -> tuple[bool, list | None]:
        """Check if webhooks have been setup correctly

        Returns: (success, topics)"""
        try:
            response = self.wcapi.get("webhooks?status=active&per_page=100")
            response.raise_for_status()

            webhooks = response.json()

            topics = []
            for webhook in webhooks:
                if webhook["delivery_url"] == delivery_url:
                    topics.append(webhook["topic"])
            return True, topics
        except (HTTPError, JSONDecodeError) as e:
            self.log("Error while getting webhooks: ", e)
            return False, None
