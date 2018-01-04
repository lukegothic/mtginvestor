import os, re, sys, csv, json, utils, requests, phppgadmin
from PIL import Image
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
    filename = "{}/{}.csv".format(cachedir, deckid);
    # guardar en disco si es necesario
    # borrar si ha pasado 1h
    if not os.path.exists(filename):
        req = requests.get("https://deckbox.org/sets/export/{}?format=csv&f=&s=&o=&columns=Image%20URL".format(deckid))
        with open(filename, "w") as f:
            f.write(req.text);
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
                    "id": id,
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
    sys.stdout.write("Normalizando inventario por multiverse_id...")
    sys.stdout.flush()
    basecards = phppgadmin.query("SELECT c.id as id, c.name as name, s.name as set, c.idmkm as idmkm, c.idck as idck, c.multiverse_id as multiverse_id FROM scr_cards c LEFT JOIN scr_sets s on c.set = s.code WHERE multiverse_id IN({})".format(",".join(multiverse_ids)))
    for card in cards:
        for basecard in basecards:
            if card["id"] == basecard["multiverse_id"]:
                card.update(basecard)
                break;
    print("OK ({} sin normalizar)".format(len(multiverse_ids) - len(basecards)))
    # hacer algo con las que no encuentra
    print("Normalizando inventario por set + name...")
    #sys.stdout.flush()
    sql = "with t(name,set) as (VALUES"
    for card in cards:
        if not isScryfallID(card["id"]):
            sql += "('{}','{}'),".format(card["name"].replace("'","''"), card["set"].replace("'","''"))
    sql = sql[:-1] + ") SELECT c.id as id, c.name as name, s.name as set, c.idmkm as idmkm, c.idck as idck, c.image_uri as image_uri FROM t LEFT JOIN scr_cards c ON c.name LIKE t.name||'%' LEFT JOIN scr_sets s on c.set = s.code ORDER BY t.name, s.name"
    basecards = phppgadmin.query(sql)
    # cargar las relaciones ya hechas
    filete = "__offlinecache__/deckbox/idlinks.txt"
    idlinks = {}
    imagehelp = False
    try:
        with open(filete) as f:
            lines = f.read().splitlines()
        for line in lines:
            ids = line.split(",")
            idlinks[ids[0]] = ids[1]
    except:
        with open(filete, "w") as f:
            pass
    for card in cards:
        if not isScryfallID(card["id"]):
            candidates = []
            for basecard in basecards:
                if basecard["name"].startswith(card["name"]):
                    candidates.append(basecard)
            #print(":: {} [{}] ::".format(card["name"], card["set"]))
            # buscamos coincidencia exacta o similar entre las opciones
            for cand in candidates:
                if cand["set"].startswith(card["set"]) or card["set"].startswith(cand["set"]) or (card["id"] in idlinks and idlinks[card["id"]] == cand["id"]):
                    #print("AUTO: {}".format(cand["set"]))
                    card.update(cand)
                    break
            # ofrecemos interfaz
            if not isScryfallID(card["id"]):
                if len(candidates) > 0:
                    if imagehelp:
                        image = Image.new("RGBA", (0, 0))
                    for k, cand in list(enumerate(candidates)):
                        print("{}. {}".format(k+1, cand["set"]))
                        if imagehelp:
                            image = utils.mergeImages(image, utils.addTextToImage(utils.resizeImageBy(utils.getImageFromURI(cand["image_uri"]), 40), "{}".format(k + 1)))
                    if imagehelp:
                        image.show()
                sel = input("Opcion: ")
                if (sel != ""):
                    sel = candidates[(int)(sel)-1]
                    with open(filete, "a") as f:
                        f.write("{},{}\n".format(card["id"], sel["id"]))
                    card.update(sel)
                else:
                    pass
            #print()
    # retirar las indomables..+***
    total = len(cards)
    for i, card in reversed(list(enumerate(cards))):
        if not isScryfallID(card["id"]):
            cards.pop(i)
    print("Finalizado, {} indomables de {}".format(total - len(cards), total))

    return cards
