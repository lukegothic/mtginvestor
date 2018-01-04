import deckbox, mkm, sys, utils
import sqlite3

cards = deckbox.getDeck(1887018)
cardnames = []
for card in cards:
    cardnames.append("name LIKE '{}%'".format(card["name"].replace("'", "''")))
cardnames = " OR ".join(cardnames)
dbconn = sqlite3.connect("__offlinecache__/scryfall/scryfall.db")
dbconn.row_factory = sqlite3.Row
c = dbconn.cursor()
dbcards = c.execute("SELECT * FROM cards WHERE {}".format(cardnames)).fetchall()
for card in cards:
    matches = []
    for dbcard in dbcards:
        if (dbcard["name"].startswith(card["name"])):
            matches.append(dbcard)
    print("{} {}".format(len(matches), card["name"]))
    for m in matches:
        if not m["idmkm"] is None:
            qcard = {
                "idmkm": m["idmkm"],
                "isFoil": False,
                "idLanguage": "EN"
            }
            mkm.getPriceData(qcard)
            print(qcard["mkmprice"])
