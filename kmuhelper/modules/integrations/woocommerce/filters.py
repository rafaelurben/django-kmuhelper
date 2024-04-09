from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from kmuhelper.modules.integrations.woocommerce.utils import is_connected


class WooCommerceStateFilter(admin.SimpleListFilter):
    """Filter that filters views based on WooCommerce state."""

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("WooCommerce State")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "wc_state"

    def __init__(self, request, params, model, model_admin):
        super(WooCommerceStateFilter, self).__init__(
            request, params, model, model_admin
        )

    def lookups(self, request, model_admin):
        return [
            ("all", _("All")),
            ("linked", _("Linked")),
            ("not_linked", _("Not linked")),
            ("deleted", _("Deleted")),
            ("not_deleted", _("Not deleted")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value() is None:
            # default option
            self.used_parameters[self.parameter_name] = "not_deleted"

        if self.value() == "linked":
            return queryset.exclude(woocommerceid=0)
        if self.value() == "not_linked":
            return queryset.filter(woocommerceid=0)
        if self.value() == "deleted":
            return queryset.filter(woocommerce_deleted=True)
        if self.value() == "not_deleted":
            return queryset.exclude(woocommerce_deleted=True)

        return queryset

    def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        for i, (lookup, title) in enumerate(self.lookup_choices):
            if add_facets:
                if (count := facet_counts.get(f"{i}__c", -1)) != -1:
                    title = f"{title} ({count})"
                else:
                    title = f"{title} (-)"
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

    def has_output(self):
        return is_connected() and super().has_output()
