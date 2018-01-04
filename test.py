import deckbox, mkm, sys, utils
#
standardsets = ["Kaladesh", "Aether Revolt", "Amonkhet", "Hour of Devastation", "Ixalan"]
mycards = deckbox.getInventory()
master = mkm.getMasterData()
stock = []
for card in mycards:
    if card["set"] in standardsets:
        stockitem = {
            "idLanguage": card["idLanguage"],
            "count": card["count"],
            "isFoil": card["isFoil"],
            "condition": "NM",
            "isSigned": False,
            "isPlayset": False
        }
        for m in master:
            if m["website"].endswith(card["idmkm"]):
                stockitem["idProduct"] = m["idProduct"]
                stockitem["rarity"] = m["rarity"]
                stockitem["website"] = m["website"]
                break
        stock.append(stockitem)
mkm.postStock(stock)

#mkm.getAllPrices()
