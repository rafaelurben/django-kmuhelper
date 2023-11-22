"""Utils for translations"""

from django.utils import translation

I18N_HELP_TEXT = translation.gettext_lazy(
    "Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'"
)

# qTranslate-X compatible translation functions


def langselect(string, lang="de"):
    if "[:" + lang + "]" in string:
        return string.split("[:" + lang + "]")[1].split("[:")[0]
    if "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    return string


# Autotranslations


def autotranslate_quantity_description(quantity_description, quantity=1):
    match quantity_description:
        case "Stück" | "Stück" | "Stück(e)":
            return translation.npgettext(
                "quantity description", "Stück", "Stück", quantity
            )
        case "Stunde" | "Stunden" | "Stunde(n)":
            return translation.npgettext(
                "quantity description", "Stunde", "Stunden", quantity
            )
        case "Einheit" | "Einheiten" | "Einheit(en)":
            return translation.npgettext(
                "quantity description", "Einheit", "Einheiten", quantity
            )
        case "Flasche" | "Flaschen" | "Flasche(n)":
            return translation.npgettext(
                "quantity description", "Flasche", "Flaschen", quantity
            )
        case "Tube" | "Tuben" | "Tube(n)":
            return translation.npgettext(
                "quantity description", "Tube", "Tuben", quantity
            )
    return quantity_description


def autotranslate_fee_name(name):
    match name:
        case "Versandkosten":
            return "[:de]Versandkosten[:fr]Frais d'envoi[:it]Spese di spedizione[:en]Delivery costs[:]"
    return name


# Django translation functions


class Language:
    """Context manager for language switching"""

    def __init__(self, language):
        self.language = language
        self.cur_language = None

    def __enter__(self):
        self.cur_language = translation.get_language()
        translation.activate(self.language)

    def __exit__(self, type, value, traceback):
        translation.activate(self.cur_language)
