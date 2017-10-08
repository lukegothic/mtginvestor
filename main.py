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
    sql = "DELETE FROM ck_buylist;INSERT INTO ck_buylist(card,name,edition,price,foil,count) VALUES"
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
    # Rehacer tabla de precios minimos
    print("Creando tabla de precios min para hoy (unos 5 minutos)")
    phppgadmin.execute("DROP MATERIALIZED VIEW mkm_cardpricesmin;CREATE MATERIALIZED VIEW mkm_cardpricesmin AS SELECT mkm_cardprices.edition,mkm_cardprices.card as name, mkm_cardprices.foil, min(mkm_cardprices.price) AS price FROM mkm_cardprices GROUP BY mkm_cardprices.edition, mkm_cardprices.card, mkm_cardprices.foil WITH DATA; ALTER TABLE mkm_cardpricesmin OWNER TO postgres;")
    print("OK")
def finance_fromeutousa():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionporgastosdeenvio = 0.05
    precioparaenviocertificado = 25
    profittargetpct = 1.1
    with open("output/eutousa.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["edition", "name", "foil", "ck", "mkm", "seller", "available", "profit", "profittotal", "profitpct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    # TODO: DEFINIR LO QUE ES POTENTIAL ---> usar cada seller de manera particular para no tener que buscarlo a mano etc
    # TODO: ELIMINAR FALSOS POSITIVOS (available = 0)
    for edition in editions:
        if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
            sql = "select ck.edition, ck.name, ck.foil, ck.price as ck, mkm.price as mkm, mkm.seller, mkm.available, (ck.price - mkm.price) as profit, (ck.price - mkm.price) * mkm.available as profittotal, round(ck.price / mkm.price, 2) - 1 profitpct from (select e.code as editioncode, e.name as edition, p.name, foil, round(cast(price * {} as numeric), 2) as price from ck_buylist p left join editions e on p.edition = e.code_ck where e.code = '{}') ck inner join (select e.code as editioncode, e.name as edition, c.name, foil, seller, LEAST(available, 17) as available, round(cast(((price * LEAST(available, 17)) + (select cost from mkm_shippingcosts sc where sc.from = p.itemlocation and sc.itemcount <= LEAST(available, 17) and tracked = p.price >= {} order by itemcount desc limit 1)) / LEAST(available, 17) as numeric), 2) as price from mkm_cardprices p left join mkm_cards c on p.card = c.id and p.edition = c.edition left join editions e on c.edition = e.code_mkm where e.code = '{}') mkm on ck.editioncode = mkm.editioncode and lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where mkm.price < ck.price and round(ck.price / mkm.price, 2) >= {}".format(usdtoeu - comisionporgastosdeenvio, edition["id"], precioparaenviocertificado, edition["id"], profittargetpct)
            cards = phppgadmin.query(sql)
            with open("output/eutousa.csv", "a", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["edition", "name", "foil", "ck", "mkm", "seller", "available", "profit", "profittotal", "profitpct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for card in cards:
                    writer.writerow(card)
def finance_fromusatoeu():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionmkm = 0.05
    undercut = 0.05
    with open("output/usatoeu.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["edition", "name", "foil", "ck", "mkm", "available", "profit", "profittotal", "profitpct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    # TODO: DEFINIR LO QUE ES POTENTIAL ---> marcar cuando es un staple y etc.
    for edition in editions:
        if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
            sql = "select ck.edition, ck.name, ck.foil, ck.price as ck, mkm.price as mkm, ck.available, (mkm.price - ck.price) as profit, (mkm.price - ck.price) * available as profittotal,(mkm.price / ck.price) - 1 as profitpct from (select e.code as editioncode, e.name as edition, c.name, foil, round(cast(price * {} as numeric), 2) as price, available from ck_cardprices p left join ck_cards c on p.card = c.id left join editions e on p.edition = e.code_ck where condition = 'NM' and available > 0 and e.code = '{}') ck inner join (select e.code as editioncode, c.name, c.edition, p.foil, round(cast(p.price * {} as numeric), 2) as price from mkm_cardpricesmin p left join mkm_cards c on p.name = c.id and p.edition = c.edition left join editions e on p.edition = e.code_mkm where e.code = '{}') mkm on ck.editioncode = mkm.editioncode and lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where ck.price < mkm.price".format(usdtoeu, edition["id"], 1 - comisionmkm - undercut, edition["id"])
            cards = phppgadmin.query(sql)
            with open("output/usatoeu.csv", "a", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["edition", "name", "foil", "ck", "mkm", "available", "profit", "profittotal", "profitpct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
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
if len(sys.argv) == 2:
    s = sys.argv[1]
    options[s]()
else:
    while True:
        opt = menu()
        if (opt == "0"):
            break
        os.system('cls')
        options[opt]()
