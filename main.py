#menu
from base import CK
from base import MKM
from base import Gatherer
from base import ExchangeRate
from base import Proxy
import phppgadmin
import sys
from lxml import html
import time
import os
import csv

def ckprocess_savebuylist():
    buylist = CK.buylist()
    sql = "INSERT INTO ck_buylist(card,name,edition,price,foil,count) VALUES"
    for card in buylist:
        for entry in card.entries:
            sql = sql + "({},'{}',{},{},{},{}),".format(card.id, card.name.replace("'","''"), card.edition, entry.price, "true" if entry.foil else "false", entry.count)
    sys.stdout.write("Guardando buylist...")
    sys.stdout.flush()
    print(phppgadmin.execute(sql[:-1]))
    sys.stdout.write("OK")
def ckprocess_savestore():
    print("todo")
def ckprocess_datosmaestros():
    CK.crawlEditions()
    CK.crawlCards()
def mkmprocess_savestore():
    editions = phppgadmin.query("select e.code_mkm as id, e.name from editions e inner join mkm_editions mkm on e.code_mkm = mkm.id left join mkm_cardprices p on p.edition = mkm.id group by e.code_mkm, e.name having count(p.card) = 0")
    for edition in editions:
        #TODO: controlamos si ya tenemos precios, se puede hacer que solo se controlen precio no actualizados y borrar precios antiguos
        print(edition["name"])
        cards = MKM.getPrices(edition)
        sql = ""
        for card in cards:
            normalcnt = 0
            foilcnt = 0
            #TODO: ignorar falsos positivos de cartas foil de ediciones que no tienen foil
            for entry in card.entries:
                if (entry.foil):
                    foilcnt += 1
                else:
                    normalcnt += 1
                sql += "('{}','{}',{},{},{},'{}','{}'),".format(card.id, card.edition, entry.price, entry.foil, entry.count, entry.seller.replace("'","''"), entry.location)
            #print("{} [{}|{}*]".format(card.name, normalcnt, foilcnt))
        if sql != "":
            affected = phppgadmin.execute("INSERT INTO mkm_cardprices(card,edition,price,foil,available,seller,itemlocation) VALUES" + sql[:-1])
            print("Total prices inserted: {}".format(affected))
            #time.sleep(120)
        else:
            print("No price data")
def finance_fromeutousa():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionporgastosdeenvio = 0.05
    with open("output/eutousa.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    # TODO: DEFINIR LO QUE ES POTENTIAL ---> usar cada seller de manera particular para no tener que buscarlo a mano etc
    # TODO: ELIMINAR FALSOS POSITIVOS (available = 0)
    for edition in editions:
        if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
            cards = phppgadmin.query("select ck.name, mkm.edition, ck.foil, ck.price as ck, mkm.price as mkm, ck.price - mkm.price as diff, ck.price / mkm.price as pct from (select edition, name, foil, price * {} as price, count as available from ck_buylist where edition = {}) CK left join (select c.edition, c.name, p.foil, min(price) price, sum(available) from mkm_cards c left join mkm_cardprices p on c.edition = p.edition and c.id = p.card where c.edition = '{}' group by c.name, c.edition, p.foil) mkm on lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where ck.price - mkm.price >= 1 and ck.price / mkm.price >= 1.2".format(usdtoeu - comisionporgastosdeenvio, edition["code_ck"], edition["code_mkm"]))
            with open("eutousa.csv", "a", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for card in cards:
                    writer.writerow(card)
def finance_fromusatoeu():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionmkm = 0.05
    undercut = 0.05
    with open("output/usatoeu.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    # TODO: DEFINIR LO QUE ES POTENTIAL ---> marcar cuando es un staple y etc.
    for edition in editions:
        if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
            cards = phppgadmin.query("select ck.name, mkm.edition, ck.foil, ck.price as ck, mkm.price as mkm, ck.price - mkm.price as diff, ck.price / mkm.price as pct from (select c.name, p.foil, price * {} as price from ck_cardprices p left join ck_cards c on p.card = c.id where condition = 'NM' and available > 0 and c.edition = {}) ck left join (select c.name, c.edition, p.foil, min(price) * {} as price from mkm_cardprices p left join mkm_cards c on p.card = c.id where c.edition = '{}' group by c.name, p.foil,c.edition) mkm on lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where ck.price / mkm.price < 1".format(usdtoeu, edition["code_ck"], 1 - comisionmkm - undercut, edition["code_mkm"]))
            with open("usatoeu.csv", "a", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for card in cards:
                    writer.writerow(card)
def menu():
    # TODO: menus gonitos con submenus
    os.system('cls')
    print("==[ MTG INVESTOR for Heroes by Luke ]==")
    print("CK")
    print("  1. Renovar buylist")
    print("  2. Renovar inventario")
    print("  3. REHACER DATOS MAESTROS")
    print("MKM")
    print("  4. Renovar inventario")
    print("  5. REHACER DATOS MAESTROS")
    print("Finanzas")
    print("  6. Europa -> USA")
    print("  7. USA -> Europa")
    print("")
    print("0. Salir")
    return input("Opcion: ")

options = {
    "1": ckprocess_savebuylist,
    "2": ckprocess_savestore,
    "3": ckprocess_datosmaestros,
    "4": mkmprocess_savestore,
    #"4": mkmprocess_savestore,
    "6": finance_fromeutousa,
    "7": finance_fromusatoeu
}
while True:
    opt = menu()
    if (opt == "0"):
        break
    os.system('cls')
    options[opt]()

#TODO: precio por vendor
# select vendor.edition,vendor.card,vendor.foil,vendor.price as vendor,mkm_cardpricesmin.price as market,vendor.price-mkm_cardpricesmin.price as diff,vendor.price/mkm_cardpricesmin.price as pct
# from (select edition, card, foil, price from mkm_cardprices cp where seller = 'GusMate') vendor
# left join mkm_cardpricesmin on vendor.edition = mkm_cardpricesmin.edition and vendor.card = mkm_cardpricesmin.card and vendor.foil = mkm_cardpricesmin.foil
# where vendor.price/mkm_cardpricesmin.price  < 1.2
