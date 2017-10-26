import deckbox, mkm, sys, utils

mycards = deckbox.getInventory()
mkm.postStock(mycards)
