# data: array de cartas
# sourcelang: source (mkm, deckbox, scryfall...)
# targetlang: target (mkm, deckbox, scryfall...)
# TODO: generalizarlo, por ahora, preparado para deckbox a mkm
# cargador dinamico, muy bonito pero no sirve en este caso
#for prop in item:
#    translateditem[prop] = (translationtable[prop][item[prop]] if item[prop] in translationtable[prop] else item[prop]) if prop in translationtable else item[prop]
import csv, json
import pprint

translationtable = {
    "language": {
        "English": {"idLanguage": 1, "languageName": "English"},
        "French": {"idLanguage": 2, "languageName": "French"},
        "German": {"idLanguage": 3, "languageName": "German"},
        "Spanish": {"idLanguage": 4, "languageName": "Spanish"},
        "Italian": {"idLanguage": 5, "languageName": "Italian"},
        "Simplified Chinese": {"idLanguage": 6, "languageName": "Simplified Chinese"},
        "Chinese": {"idLanguage": 7, "languageName": "Chinese"},
        "Japanese": {"idLanguage": 8, "languageName": "Japanese"},
        "Portuguese": {"idLanguage": 9, "languageName": "Portuguese"},
        "Russian": {"idLanguage": 10, "languageName": "Russian"},
        "Korean": {"idLanguage": 11, "languageName": "Korean"},
        "Traditional Chinese": {"idLanguage": 12, "languageName": "Traditional Chinese"}
    },
    "condition": {
        "Mint": "MT",
        "Near Mint": "NM",
        "Excellent": "EX"
    },
    "set": {
        "European Land Program":"Euro Lands",
        "Release Events":"Release Promos",
        "Prerelease Events: Dragons of Tarkir":"Dragons Of Tarkir: Promos",
        "Premium Deck Series: Fire and Lightning":"Premium Deck Series: Fire \u0026 Lightning",
        "Magic Player Rewards":"Player Rewards Promos",
        "Grand Prix":"Grand Prix Promos",
        "Magic 2015 Core Set":"Magic 2015",
        "Battle Royale Box Set":"Battle Royale",
        "Prerelease Events":"Prerelease Promos",
        "Revised Edition":"Revised",
        "Prerelease Events: Khans of Tarkir":"Khans of Tarkir: Promos",
        "Magic Game Day Cards":"Game Day Promos",
        "Guilds of Ravnica Guild Kit":"Guilds of Ravnica: Guild Kits",
        "Arena League":"Arena League Promos",
        "Classic Sixth Edition":"Sixth Edition",
        "Duel Decks: Phyrexia vs. the Coalition":"Duel Decks: Phyrexia vs. The Coalition",
        "Two-Headed Giant Tournament":"KAKA",
        "Launch Parties":"Prerelease Promos",
        "Friday Night Magic":"Friday Night Magic Promos",
        "Super Series":"Junior Super Series Promos",
        "Prerelease Events: Aether Revolt":"Aether Revolt: Promos",
        "Prerelease Events: Rivals of Ixalan":"Rivals of Ixalan: Promos",
        "Judge Gift Program":"Judge Rewards Promos",
        "Prerelease Events: Dominaria":"Dominaria: Promos",
        "Modern Masters 2017 Edition":"Modern Masters 2017",
        "Magic 2014 Core Set":"Magic 2014",
        "Media Inserts":"KAKA2",
        "Prerelease Events: Fate Reforged":"Fate Reforged: Promos",
        "WPN/Gateway":"Gateway Promos",
        "Limited Edition Beta":"Beta",
        "Time Spiral \"Timeshifted\"":"Time Spiral",
        "Prerelease Events: Eldritch Moon":"Eldritch Moon: Promos",
        "Core Set 2019": "Core 2019",
        "Prerelease Events: Battle for Zendikar":"Battle for Zendikar: Promos",
        "Modern Masters 2015 Edition":"Modern Masters 2015",
        "Summer of Magic":"Summer Magic",
        "Asia Pacific Land Program":"APAC Lands"
    }
}
global mkm_sets
with open("data/mkm/sets.json", "r", encoding="utf8") as f:
    mkm_sets = json.load(f)
mkm_sets = mkm_sets["expansion"]

global mkm_cards
mkm_cards = []
with open("data/mkm/cards.csv", "r", encoding="utf8") as f:
    reader = csv.DictReader(f, delimiter=",", quotechar='"')
    for row in reader:
        if row["Category ID"] == "1":
            mkm_cards.append({
                "idProduct": (int)(row["idProduct"]),
                "name": row["Name"],
                "set": (int)(row["Expansion ID"])
            })

def traduceitem(item):
    # pasada 1: definir objeto
    translateditem = {
        "idProduct": None,
        "idArticle": None,
        "count": item["count"],
        "language": translationtable["language"][item["language"]] if item["language"] in translationtable["language"] else 1,
        "comments": None,
        "price": None,
        "condition": translationtable["condition"][item["condition"]]  if item["condition"] in translationtable["condition"] else "NM",
        "isFoil": item["isFoil"],
        "isSigned": False,
        "isPlayset": False
    }
    # pasada 2: encontrar producto con propiedades del objeto
    # 2.1 edicion
    set_name = translationtable["set"][item["set_name"]] if item["set_name"] in translationtable["set"] else item["set_name"] # TODO: cambiar esto para escupir el item["set"]
    set_id = None

    if not set_name is None:
        for s in mkm_sets:
            if set_name == s["enName"]:
                set_id = s["idExpansion"]
                break
    # 2.2 product (usando name y idExpansion)
    if not set_id is None:
        item_name = item["name"].lower()
        for c in mkm_cards:
            card_name = c["name"].lower()
            if item_name == card_name or card_name.startswith(item_name):
                if set_id == c["set"]:
                    translateditem["idProduct"] = c["idProduct"]
                    break
    return translateditem

#Count,Tradelist Count,Name,Edition,Card Number,Condition,Language,Foil,Signed,Artist Proof,Altered Art,Misprint,Promo,Textless,My Price,Image URL
#2,0,Abandoned Sarcophagus,Hour of Devastation,158,Near Mint,English,foil,,,,,,,0,https://deckbox.org/system/images/mtg/cards/430847.jpg
def traduce(data, sourcelang = "deckbox", targetlang = "mkm"):
    translateddata = []
    nontraslated = []
    for d in data:
        translateditem = traduceitem(d)
        if not translateditem["idProduct"] is None:
            translateddata.append(traduceitem(d))
        else:
            pprint.pprint(d)
            nontraslated.append(d)
    return (translateddata, nontraslated)
