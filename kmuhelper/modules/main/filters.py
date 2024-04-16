from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _


class ProductTypeFilter(admin.SimpleListFilter):
    """Filter that filters views based on whether products are variants or not."""

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("product type")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "type"

    def __init__(self, request, params, model, model_admin):
        super(ProductTypeFilter, self).__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return [
            ("all", _("All")),
            ("simple", _("Simple product")),
            ("variable", _("Variable product")),
            ("variant", _("Product variant")),
            ("no_variant", _("Not a product variant")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value() is None:
            # default option
            self.used_parameters[self.parameter_name] = "no_variant"

        if self.value() == "simple":
            return (
                queryset.filter(parent_id=None)
                .prefetch_related("children")
                .annotate(variants_count=Count("children"))
                .filter(variants_count=0)
            )
        if self.value() == "variable":
            return (
                queryset.filter(parent_id=None)
                .prefetch_related("children")
                .annotate(variants_count=Count("children"))
                .filter(variants_count__gt=0)
            )
        if self.value() == "variant":
            return queryset.exclude(parent_id=None)
        if self.value() == "no_variant":
            return queryset.filter(parent_id=None)

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
