import deckbox, mkm, sys, utils
import sqlite3, csv
#
# postear para vender las cosas que son de standard
# standardsets = ["Kaladesh", "Aether Revolt", "Amonkhet", "Hour of Devastation", "Ixalan"]
# mycards = deckbox.getInventory()
# master = mkm.getMasterData()
# stock = []
# for card in mycards:
#     if card["set"] in standardsets:
#         stockitem = {
#             "idLanguage": card["idLanguage"],
#             "count": card["count"],
#             "isFoil": card["isFoil"],
#             "condition": "NM",
#             "isSigned": False,
#             "isPlayset": False
#         }
#         for m in master:
#             if m["website"].endswith(card["idmkm"]):
#                 stockitem["idProduct"] = m["idProduct"]
#                 stockitem["rarity"] = m["rarity"]
#                 stockitem["website"] = m["website"]
#                 break
#         stock.append(stockitem)
# mkm.postStock(stock)

#mkm.getAllPrices()
# cards = deckbox.getDeck(1887018)
# cardnames = []
# for card in cards:
#     cardnames.append("name LIKE '{}%'".format(card["name"].replace("'", "''")))
# cardnames = " OR ".join(cardnames)
# dbconn = sqlite3.connect("__offlinecache__/scryfall/scryfall.db")
# dbconn.row_factory = sqlite3.Row
# c = dbconn.cursor()
# dbcards = c.execute("SELECT * FROM cards WHERE {}".format(cardnames)).fetchall()
# for card in cards:
#     matches = []
#     for dbcard in dbcards:
#         if (dbcard["name"].startswith(card["name"])):
#             matches.append(dbcard)
#     print("{} {}".format(len(matches), card["name"]))
#     for m in matches:
#         if not m["idmkm"] is None:
#             qcard = {
#                 "idmkm": m["idmkm"],
#                 "isFoil": False,
#                 "idLanguage": "EN"
#             }
#             mkm.getPriceData(qcard)
#             print(qcard["mkmprice"])

cards = deckbox.getInventory()

with open("output/myinvprice.csv", "w", newline='\n') as f:
    writer = csv.DictWriter(f, fieldnames=cards[0].keys(), delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for card in cards:
        writer.writerow(card)
