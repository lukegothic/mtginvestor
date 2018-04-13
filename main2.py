import os, re, sys, json, requests, decklist, sqlite3, csv, webbrowser
import utils
import deckbox

import tkinter as tk
from tkinter import filedialog

import xml.etree.ElementTree as ET

basedir = "__mycache__/scryfall"
if (not os.path.exists(basedir)):
    os.makedirs(basedir)
dbdir = "__offlinecache__/scryfall"
if (not os.path.exists(dbdir)):
    os.makedirs(dbdir)
dbfile = "{}/scryfall.db".format(dbdir)
def create_db():
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sets
             (code text PRIMARY KEY, name text, set_type text, released_at text, block_code text, block text, parent_set_code text, card_count integer, digital integer, foil integer, icon_svg_uri text, search_uri text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cards
             (id text, mtgo_id integer, name text, setcode text, idmkm text, idck text, color text, type text, usd real, eur real, tix real, reprint integer, image_uri text, collector_number integer, multiverse_id integer, modernlegal integer)''')
    dbconn.commit()
    dbconn.close()
def updatedb(softupdate=True):
    process_sets(softupdate)
    process_cards(softupdate)
def process_sets(softupdate):
    cachedir = "{}/sets".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    if not softupdate:
        for f in os.listdir(cachedir):
            os.remove("{}/{}".format(cachedir, f))
    filete = "{}/sets.json".format(cachedir)
    try:
        with open(filete) as f:
            data = f.read()
    except:
        req = requests.get("https://api.scryfall.com/sets")
        data = req.text
        with open(filete, "w") as f:
            f.write(data)
    sets = json.loads(data)
    setsinsert = []
    for set in sets["data"]:
        setsinsert.append(
            (
                set["code"],
                set["name"],
                set["set_type"],
                '{}'.format(set["released_at"]) if "released_at" in set else None,
                '{}'.format(set["block_code"]) if "block_code" in set else None,
                '{}'.format(set["block"].replace("'", "''")) if "block" in set else None,
                '{}'.format(set["parent_set_code"]) if "parent_set_code" in set else None,
                set["card_count"],
                (1 if set["digital"] else 0) if "digital" in set else 0,
                (1 if set["foil"] else 0) if "foil" in set else 0,
                set["icon_svg_uri"],
                set["search_uri"]
            )
        )
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute("DELETE FROM sets")
    c.executemany('INSERT INTO sets VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', setsinsert)
    dbconn.commit()
    print("Insertados {} de {} sets".format(c.execute("SELECT count(*) as cnt FROM sets").fetchone()[0], len(setsinsert)))
    dbconn.close()
def getCardColor(colors):
    return "C" if len(colors) == 0 else ("M" if len(colors) > 1 else colors[0])
def process_cards(softupdate):
    cachedir = "{}/cards".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    if not softupdate:
        for f in os.listdir(cachedir):
            os.remove("{}/{}".format(cachedir, f))
    reIDMKM = "https:\/\/www\.cardmarket\.com\/Magic\/Products\/Singles\/(.*?)\?"
    reIDCK = "https:\/\/www\.cardkingdom\.com\/catalog\/item\/(\d*)?\?"
    page = 1
    cardsinsert = []
    while True:
        filete = "{}/{}.json".format(cachedir, page)
        try:
            with open(filete, encoding="utf-8") as f:
                data = f.read()
        except:
            req = requests.get("https://api.scryfall.com/cards?page={}".format(page))
            data = req.text
            with open(filete, "w", encoding="utf-8") as f:
                f.write(data)
        cards = json.loads(data)
        for card in cards["data"]:
            idmkm = re.match(reIDMKM, card["purchase_uris"]["magiccardmarket"])
            idmkm = None if idmkm is None else idmkm.group(1)
            idck = re.match(reIDCK, card["purchase_uris"]["card_kingdom"])
            idck = None if idck is None else idck.group(1)
            # if (not "image_uris" in card):
            #     image_uris = []
            #     if ("card_faces" in card):
            #         for face in card["card_faces"]:
            #             image_uris.append(face["image_uris"]["normal"])
            #     image_uris = ";".join(image_uris)
            # else:
            #     image_uris = card["image_uris"]["normal"]
            try:
                cardsinsert.append(
                    (
                        card["id"],
                        card["mtgo_id"] if "mtgo_id" in card else None,
                        card["name"].split(" // ")[0],
                        card["set"],
                        idmkm,
                        idck,
                        #getCardColor(card["colors"]) if "colors" in card else (";".join(getCardColor(f["colors"]) for f in card["card_faces"])),
                        getCardColor(card["colors"]) if "colors" in card else getCardColor(card["card_faces"][0]["colors"]),
                        #card["type_line"] if "type_line" in card else (";".join(f["type_line"] for f in card["card_faces"])),
                        card["type_line"] if "type_line" in card else card["card_faces"][0]["type_line"],
                        card["usd"] if "usd" in card else None,
                        card["eur"] if "eur" in card else None,
                        card["tix"] if "tix" in card else None,
                        1 if card["reprint"] else 0,
                        #card["image_uris"]["normal"] if "image_uris" in card else (";".join(f["image_uris"]["normal"] for f in card["card_faces"])),
                        card["image_uris"]["normal"] if "image_uris" in card else card["card_faces"][0]["image_uris"]["normal"],
                        card["collector_number"],
                        card["multiverse_ids"][0] if "multiverse_ids" in card and len(card["multiverse_ids"]) > 0 else None,
                        1 if card["legalities"]["modern"] == "legal" else 0
                    )
                )
            except:
                print("No insertado: " + card["name"])
                #print("Pagina {}: {}".format(page, phppgadmin.execute(sql[:-1])))
        if (cards["has_more"]):
            page += 1
        else:
            break
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute("DELETE FROM cards")
    c.executemany('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', cardsinsert)
    dbconn.commit()
    print("Insertadas {} de {} cartas".format(c.execute("SELECT count(*) as cnt FROM cards").fetchone()[0], len(cardsinsert)))
    dbconn.close()
def download_images():
    picsdir = "{}/pics".format(basedir)
    if (not os.path.exists(picsdir)):
        os.makedirs(picsdir)
    cards = phppgadmin.query("SELECT image_uri, name, set, collector_number from scr_cards")
    reVersions = "\d*([abcd]+)"
    for c in cards:
        print("{} [{}]".format(c["name"], c["set"]))
        if c["image_uri"] != "":
            setcode = c["set"].upper()
            if setcode == "CON":
                setcode = "CFX"
            setdir = "{}/{}".format(picsdir, setcode)
            if (not os.path.exists(setdir)):
                os.makedirs(setdir)
            # controlar cartas antiguas con varias versiones
            isVersioned = re.match(reVersions, c["collector_number"])
            v = ""
            if "//" not in c["name"] and not isVersioned is None:
                v = isVersioned.group(1)
                if v == "a":
                    v = 1
                elif v == "b":
                    v = 2
                elif v == "c":
                    v = 3
                elif v == "d":
                    v = 4
            # controlar double faced
            faces = []
            if "||" in c["image_uri"]:
                print(c)
                names = c["name"].split(" // ")
                imgs = c["image_uri"].split("||")
                faces.append({ "name": names[0], "img": imgs[0] })
                faces.append({ "name": names[1], "img": imgs[1] })
                print(faces)
            else:
                # TODO: las tierras basicas tienen versiones... no se como hacerlo
                # TODO: si la carta es de flip pero no de transform, nos quedamos sólo con la parte primera del nombre!
                # TODO: EMN graf rats1 ??? por que le pone numero?
                # TODO: estas 3 tienen version 1 y 2
                # Ertai, the Corrupted[PLS]
                # Skyship Weatherlight[PLS]
                # Tahngarth, Talruum Hero[PLS]
                faces.append({ "name": c["name"].replace(" // ", "").replace('"',"").replace(":","").replace("á", "a").replace("à", "a").replace("â", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ú", "u").replace("û", "u").replace("?",""), "img": c["image_uri"] })
            for face in faces:
                filete = "{}/{}{}.full.jpg".format(setdir, face["name"], v)
                try:
                    with open(filete) as f:
                        pass
                except:
                    req = requests.get(face["img"])
                    with open(filete, "wb") as f:
                        f.write(req.content)
        else:
            print("No hay imagen")
def getcardprices(cards):
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = sqlite3.Row
    c = dbconn.cursor()
    sql = "SELECT name,min(eur) as price FROM cards WHERE LOWER(name) IN ('{}') GROUP BY name".format("','".join(cards).lower())
    dbcards = c.execute(sql)
    dbcards = dbcards.fetchall()
    dbconn.close()
    return dbcards
def getcards(cards):
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = utils.dict_factory
    c = dbconn.cursor()
    dbcards = c.execute("SELECT c.id, c.name, c.setcode, c.color, c.type, c.eur, c.image_uri, c.collector_number, s.name as setname, s.icon_svg_uri as seticon, s.released_at as setreleasedate FROM cards c LEFT JOIN sets s ON c.setcode = s.code WHERE s.digital = 0 AND LOWER(c.name) IN ('{}') ORDER BY s.released_at".format("','".join(cards).lower()))
    dbcards = dbcards.fetchall()
    dbconn.close()
    return dbcards
def pricedecklist():
    deck = decklist.readdeckfromfile()
    prices = getcardprices(c.replace("'", "''") for c in deck)
    total = 0
    with open("prices.csv", "w") as f:
        for card in deck:
            quantity = deck[card]
            for cp in prices:
                cardnameprice = cp["name"]
                cardprice = cp["price"]
                if card.lower() == cardnameprice.lower():
                    cardtotal = cardprice * quantity
                    f.write("{};{};{:.2f};{:.2f}\n".format(quantity, card, cardprice, cardtotal))
                    total += cardtotal
                    break;
    print("Total = {:.2f} Euros".format(total))
def cardsbyedition():
    deck = decklist.readdeckfromfile()
    cards = getcards(c.replace("'", "''") for c in deck)
    utils.showCardsInViewer(cards)
def vendiblesmodern():
    inventory = deckbox.getInventory()
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = utils.dict_factory
    c = dbconn.cursor()
    dbcards = c.execute("SELECT c.name, s.name as setname, usd, multiverse_id as id FROM cards c LEFT JOIN sets s ON c.setcode = s.code WHERE modernlegal = 1 AND usd >= 10 ORDER BY s.released_at").fetchall()
    dbconn.close()
    vendibles = []
    for card in inventory:
        for dbcard in dbcards:
            if card["id"] == dbcard["id"] or (card["name"].lower() == dbcard["name"].lower() and card["set"].lower() == dbcard["setname"].lower()):
                card["price"] = dbcard["usd"]
                vendibles.append(card)
                break
    for card in vendibles:
        print("{}x {} [{}] {}".format(card["count"], card["name"], card["set"], card["price"]))
def preciosusavseu():
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = utils.dict_factory
    c = dbconn.cursor()
    dbcards = c.execute("SELECT c.name, s.name as setname, usd * 0.8 as usd, eur FROM cards c LEFT JOIN sets s ON c.setcode = s.code WHERE not usd is null AND not eur is null ORDER BY s.released_at LIMIT 10").fetchall()
    dbconn.close()
    for card in dbcards:
        print(card)
def cardsbymtgoid(mtgoids):
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = utils.dict_factory
    c = dbconn.cursor()
    dbcards = c.execute("SELECT c.mtgo_id, c.name, s.name as setname, tix FROM cards c LEFT JOIN sets s ON c.setcode = s.code WHERE c.mtgo_id IN ({}) ORDER BY s.released_at".format(mtgoids)).fetchall()
    dbconn.close()
    return dbcards
def inversionmtgo():
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename()
    with open(filepath) as f:
        data = f.readlines()
    cards = {}
    for d in data:
        dat = d.replace("\n", "").split(";")
        cards[dat[0]] = { "name": None, "set": None, "buy": (float)(dat[3]), "current": None, "min": None, "max": None }
    dbcards = cardsbymtgoid(",".join(c for c in cards))
    print(cards)
    for card in dbcards:
        id = str(card["mtgo_id"])
        cards[id]["name"] = card["name"]
        cards[id]["set"] = card["setname"]
        cards[id]["current"] = card["tix"]
    with open("7_inversion.csv", "w") as f:
        for c in cards:
            f.write("{};{};{};{};{}\n".format(c, cards[c]["name"], cards[c]["set"], cards[c]["buy"], cards[c]["current"]));
def valoramtgo():
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename()
    tree = ET.parse(filepath)
    t = tree.getroot()
    cards = {}
    total = 0
    for card in t.iter("Cards"):
        cards[(int)(card.attrib["CatID"])] = { "Quantity": (int)(card.attrib["Quantity"]), "Name": card.attrib["Name"] }
    # primera pasada, no sabemos si son normales o foil, consultamos todas
    dbcards = cardsbymtgoid(",".join(str(c) for c in cards))
    for card in dbcards:
        id = card["mtgo_id"]
        cards[id]["tix"] = card["tix"]
    # segunda pasada, consultamos las foils con downgrade a normal
    cards2 = {}
    for card in cards:
        if not "tix" in cards[card]:
            newid = card - 1
            cards2[newid] = { "Quantity": cards[card]["Quantity"], "Name": cards[card]["Name"] }
        else:
            total = total + (cards[card]["tix"] * cards[card]["Quantity"])
    dbcards = cardsbymtgoid(",".join(str(c) for c in cards2))
    for card in dbcards:
        id = card["mtgo_id"]
        cards2[id]["tix"] = card["tix"]
    # tercera pasada, output de las cartas kk
    for card in cards2:
        if not "tix" in cards2[card] or cards2[card]["tix"] is None:
            print(card + 1, cards2[card])
        else:
            total = total + (cards2[card]["tix"] * cards2[card]["Quantity"])
    print("Total", total)
def menu():
    os.system('cls')
    print("==[ DB retriever ]==")
    print("  1. Update DB")
    print("  2. Get images")
    print("  3. Price deck")
    print("  4. Todas las ediciones de una lista de cartas")
    print("  5. Vendibles modern")
    print("  6. Precios USA vs EU")
    print("  7. Inversiones MTGO")
    print("  8. Valora MTGO")
    print("  0. Salir")
    return input("Opcion: ")

create_db()
options = {
    "1": updatedb,
    "2": download_images,
    "3": pricedecklist,
    "4": cardsbyedition,
    "5": vendiblesmodern,
    "6": preciosusavseu,
    "7": inversionmtgo,
    "8": valoramtgo
}
if len(sys.argv) == 2:
    s = sys.argv[1]
    options[s]()
else:
    while True:
        opt = menu()
        if (opt == "0" or opt == ""):
            break
        os.system('cls')
        options[opt]()
        input("PRESIONA UNA TECLA PARA CONTINUAR")
