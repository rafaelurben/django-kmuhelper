"""Utils for automatic translations of strings."""

I18N_HELP_TEXT = "Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'"

# qTranslate-X compatible translation functions

def langselect(string, lang="de"):
    if "[:"+lang+"]" in string:
        return string.split("[:"+lang+"]")[1].split("[:")[0]
    if "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    return string

# Autotranslations

def autotranslate_mengenbezeichnung(mengenbezeichnung):
    match mengenbezeichnung:
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
    return mengenbezeichnung

def autotranslate_kosten_name(name):
    match name:
        case "Versandkosten":
            return "[:de]Versandkosten[:fr]Frais d'envoi[:it]Spese di spedizione[:en]Delivery costs[:]"
    return name
