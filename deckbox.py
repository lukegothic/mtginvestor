import os, re, sys, csv, json, utils, requests, phppgadmin
#from PIL import Image
import sqlite3
cachedir = "__mycache__/deckbox"
reID = "(\d*).jpg$"
translator = {
    "language": {
        "English": 1,
        "French": 2,
        "German": 3,
        "Spanish": 4,
        "Italian": 5,
        "Simplified Chinese": 6,
        "Chinese": 6,
        "Japanese": 7,
        "Portuguese": 8,
        "Russian": 9,
        "Korean": 10,
        "Traditional Chinese": 11
    },
    "condition": {
        "Mint": "MT",
        "Near Mint": "NM",
        "Excellent": "EX"
    }
}
def isScryfallID(id):
    return id.find("-") != -1
def getExportedData(deckid):
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    filename = "{}/{}.csv".format(cachedir, deckid)
    # guardar en disco si es necesario
    # borrar si ha pasado 1h
    if not os.path.exists(filename):
        req = requests.get("https://deckbox.org/sets/export/{}?format=csv&f=&s=&o=&columns=Image%20URL".format(deckid))
        with open(filename, "w") as f:
            f.write(req.text)
    sys.stdout.write("OK")
    print("")
    return filename
def getDeck(deckid):
    cards = []
    filename = getExportedData(deckid)
    with open(filename) as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            cards.append({
                "id": re.search(reID, row["Image URL"]).group(1),
                "name": row["Name"]
            })
    return cards
def getInventory(force=False):
    sys.stdout.write("Obteniendo inventario...")
    sys.stdout.flush()
    filename = getExportedData("125700")
    #leer y convertir en dict
    sys.stdout.write("Leyendo inventario...")
    sys.stdout.flush()
    cards = []
    multiverse_ids = []
    withoutset = 0
    with open(filename) as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            # sacamos el multiverse_id de la url de la imagen, yay!
            id = re.search(reID, row["Image URL"]).group(1)
            # ignoramos las que no tienen set, pero mostramos un contador de cuantas no tienen
            if row["Edition"] != "":
                cards.append({
                    "id": (int)(id),
                    "name": row["Name"],
                    "set": row["Edition"],
                    "count": (int)(row["Count"]),
                    "idLanguage": translator["language"][row["Language"]],
                    "isFoil": True if row["Foil"] == "foil" else False,
                    "condition": translator["condition"][row["Condition"]]
                })
                if not id in multiverse_ids:
                    multiverse_ids.append(id)
            else:
                withoutset += 1
    print("OK ({} sin set)".format(withoutset))
    #
    # sys.stdout.write("Normalizando inventario por multiverse_id...")
    # sys.stdout.flush()
    # dbconn = sqlite3.connect("__offlinecache__/scryfall/scryfall.db")
    # dbconn.row_factory = sqlite3.Row
    # c = dbconn.cursor()
    # sql = "SELECT c.name as card, usd, eur, multiverse_id as id FROM cards c LEFT JOIN sets s on c.setcode = s.code WHERE multiverse_id IN({})".format(",".join(multiverse_ids))
    # dbcards = c.execute(sql).fetchall()
    # print("OK ({} no encontradas)".format(len(multiverse_ids) - len(dbcards)))
    # for card in cards:
    #     for dbcard in dbcards:
    #         if card["id"] == dbcard["id"]:
    #             card["usd"] = dbcard["usd"]
    #             card["eur"] = dbcard["eur"]
    #             break
    return cards
def getInventoryRaw(force=False):
    multiverse_id_regex = r"(\d*).jpg$"
    filename = getExportedData("125700")
    cards = []
    with open(filename) as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            # asumir que habra una clase "card" que se instancia con propiedades...
            # tambien asumir que hay otra clase "inventorycard" que anade count, condition, language, isFoil
            # en este caso es una inventory card que tiene como propiedad count
            cards.append({
                # aqui las propiedades base
                "multiverse_id": (int)(re.search(multiverse_id_regex, row["Image URL"]).group(1)),
                "name": row["Name"],
                "set": None,
                "set_name": row["Edition"],
                "collector_number": (int)(row["Card Number"]) if row["Card Number"] != "" else None,
                # aqui las propiedades de inv
                "count": (int)(row["Count"]),
                "condition": row["Condition"],
                "language": row["Language"],
                "isFoil": True if row["Foil"] == "foil" else False,
                
            })
    return cards