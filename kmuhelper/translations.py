"""Utils for translations"""

from django.utils import translation

I18N_HELP_TEXT = translation.gettext_lazy("Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'")

# qTranslate-X compatible translation functions

def langselect(string, lang="de"):
    if "[:"+lang+"]" in string:
        return string.split("[:"+lang+"]")[1].split("[:")[0]
    if "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    return string

# Autotranslations

def autotranslate_quantity_description(quantity_description):
    match quantity_description:
        case "Stück":
            return "[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]"
        case "Stunden":
            return "[:de]Stunden[:fr]Heures[:it]Ore[:en]Hours[:]"
        case "Einheiten":
            return "[:de]Einheiten[:fr]Unités[:it]Unità[:en]Units[:]"
        case "Flasche":
            return "[:de]Flasche[:fr]Bouteille[:it]Bottiglia[:en]Bottle[:]"
        case "Tube":
            return "[:de]Tube[:fr]Tube[:it]Tubetto[:en]Tube[:]"
    return quantity_description

def autotranslate_kosten_name(name):
    match name:
        case "Versandkosten":
            return "[:de]Versandkosten[:fr]Frais d'envoi[:it]Spese di spedizione[:en]Delivery costs[:]"
    return name

# Django translation functions

class Language():
    """Context manager for language switching"""

    def __init__(self, language):
        self.language = language
        self.cur_language = None

    def __enter__(self):
        self.cur_language = translation.get_language()
        translation.activate(self.language)

    def __exit__(self, type, value, traceback):
        translation.activate(self.cur_language)
