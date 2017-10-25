import deckbox, mkm

mycards = deckbox.getInventory()
for ci, card in reversed(list(enumerate(mycards))):
    for ei, entry in reversed(list(enumerate(card["entries"]))):
        if entry["idLanguage"] == 1:    #excluimos las cartas en ingles, por ahora las respetamos
            card["entries"].pop(ei)
    if len(card["entries"]) == 0:
        mycards.pop(ci)

mkm.postStock(mycards)
