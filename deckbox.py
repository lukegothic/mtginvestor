import os, re, sys, csv, requests
import phppgadmin

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

def getInventory(force=False):
    dbinventoryid = "125700"
    cachedir = "__mycache__/deckbox/inventory"
    sys.stdout.write("Obteniendo inventario...")
    sys.stdout.flush()
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    filename = "{}/{}.csv".format(cachedir, dbinventoryid);
    #guardar en disco si es necesario
    if force or not os.path.exists(filename):
        req = requests.get("https://deckbox.org/sets/export/{}?format=csv&f=&s=&o=&columns=Image%20URL".format(dbinventoryid))
        with open(filename, "w") as f:
            f.write(req.text);
    sys.stdout.write("OK")
    print("")
    #leer y convertir en dict
    sys.stdout.write("Leyendo inventario...")
    sys.stdout.flush()
    reID = "(\d*).jpg$"
    cards = []
    multiverse_ids = []
    with open(filename) as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            # sacamos el multiverse_id de la url de la imagen, yay!
            id = re.search(reID, row["Image URL"]).group(1)
            card = None
            for c in cards:
                if (c["id"] == id):
                    card = c
                    break
            if (card is None):
                card = ({
                    "id": id,
                    "name": row["Name"],
                    "set": row["Edition"],
                    "entries": []
                })
                cards.append(card)
                multiverse_ids.append(id)
            card["entries"].append({
                "count": (int)(row["Count"]),
                "idLanguage": translator["language"][row["Language"]],
                "isFoil": True if row["Foil"] == "foil" else False,
                "condition": translator["condition"][row["Condition"]]
            })
    basecards = phppgadmin.query("SELECT c.name as cardname, s.name as editionname, c.idmkm as idmkm, c.idck as idck, c.multiverse_id as id FROM scr_cards c LEFT JOIN scr_sets s on c.set = s.code WHERE multiverse_id IN({})".format(",".join(multiverse_ids)))
    print("encontradas {} de {}".format(len(basecards), len(multiverse_ids)))
    for card in cards:
        for basecard in basecards:
            if card["id"] == basecard["id"]:
                card.update(basecard)
                break;
    # hacer algo con las que no encuentra
    return cards
