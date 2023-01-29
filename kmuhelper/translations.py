"""Utils for automatic translations of strings."""

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
