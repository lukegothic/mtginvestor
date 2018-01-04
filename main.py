#menu
from base import CK,MKM,Gatherer,ExchangeRate,Proxy
import phppgadmin
import sys
from lxml import html
import time
import os
import csv

def ckprocess_savebuylist():
    buylist = CK.buylist()
    # backup y borrado de datos
    print("{} precios guardados en histórico buylist".format(phppgadmin.execute("INSERT INTO ck_buylist_history(id,foil,price,available,timestamp) SELECT id,foil,price,available,timestamp FROM ck_buylist")))
    print("{} precios borrados de buylist actual".format(phppgadmin.execute("DELETE FROM ck_buylist")))
    sql = "INSERT INTO ck_buylist(id,foil,price,available) VALUES"
    for card in buylist:
        for entry in card.entries:
            sql = sql + "({},{},{},{}),".format(card.id, "true" if entry.foil else "false", entry.price, entry.count)
    sys.stdout.write("Guardando buylist...")
    sys.stdout.flush()
    print("{} precios guardados en buylist actual".format(phppgadmin.execute(sql[:-1])))
    sys.stdout.write("OK")
def ckprocess_savestore():
    print("todo")
def ckprocess_datosmaestros():
    CK.crawlEditions()
    CK.crawlCards()
def mkmprocess_savestore():
    #phppgadmin.execute("delete from mkm_cardprices")
    sqlnextedition = "select e.code_mkm as id, e.name from editions e inner join mkm_editions mkm on e.code_mkm = mkm.id left join mkm_cardprices p on p.edition = mkm.id group by e.code_mkm, e.name, mkm.locked having count(p.card) = 0 and not mkm.locked limit 1"
    while True:
        editions = phppgadmin.query(sqlnextedition)
        if (len(editions) == 1):
            edition = editions[0]
            phppgadmin.execute("update mkm_editions set locked = true where id = '{}'".format(edition["id"]))
            print(edition["name"])
            cards = MKM.getPrices(edition)
            sql = ""
            for card in cards:
                for entry in card.entries:
                    sql += "('{}','{}',{},{},{},'{}','{}'),".format(card.id, card.edition, entry.price, entry.foil, entry.count, entry.seller.replace("'","''"), entry.location)
            if sql != "":
                affected = phppgadmin.execute("INSERT INTO mkm_cardprices(card,edition,price,foil,available,seller,itemlocation) VALUES" + sql[:-1])
                print("Total prices inserted: {}".format(affected))
            else:
                print("No price data")
            phppgadmin.execute("update mkm_editions set locked = false where id = '{}'".format(edition["id"]))
        else:
            break
    # Rehacer tabla de precios minimos cuando no hay mas ediciones a procesar
    if (phppgadmin.count("select id from mkm_editions where locked") == 0):
        print("Creando tabla de precios min para hoy (unos 5 minutos)")
        phppgadmin.execute("DROP MATERIALIZED VIEW mkm_cardpricesmin;CREATE MATERIALIZED VIEW mkm_cardpricesmin AS SELECT mkm_cardprices.edition,mkm_cardprices.card as name, mkm_cardprices.foil, min(mkm_cardprices.price) AS price FROM mkm_cardprices GROUP BY mkm_cardprices.edition, mkm_cardprices.card, mkm_cardprices.foil WITH DATA; ALTER TABLE mkm_cardpricesmin OWNER TO postgres;")
        print("Finished")

    # TODO: churro para mkm
    # select '"' || edition || '/' || name || case when foil then 'F' else 'N' end || '":' || cast(round(cast(price as numeric),2) as varchar) || ',' from mkm_cardpricesmin
def finance_fromeutousa():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionporgastosdeenvio = 0.05
    precioparaenviocertificado = 25
    profittargetpct = 1.1

    sql = "select s.name as set, c.name as card, ck.foil as foil, ck.price * {0} as ck, mkm_offers.price as mkm, mkm_offers.seller as seller, mkm_offers.available as available from ck_buylist ck left join scr_cards c on ck.id = c.idck left join scr_sets s on c.set = s.code inner join (select id, foil, round(cast(((price * LEAST(available, 17)) + (select cost from mkm_shippingcosts sc where sc.from = itemlocation and sc.itemcount <= LEAST(available, 17) and tracked = price >= 25 order by itemcount desc limit 1)) / LEAST(available, 17) as numeric), 2) as price, LEAST(available, 17) as available, seller from mkm_cardprices) mkm_offers on mkm_offers.id = c.idmkm and mkm_offers.foil = ck.foil where mkm_offers.price < ck.price * {0}".format(usdtoeu - comisionporgastosdeenvio)
    cards = phppgadmin.query(sql)

    with open("output/eutousa.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["set", "card", "foil", "ck", "mkm", "seller", "available"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for card in cards:
            writer.writerow(card)

    # # TODO: DEFINIR LO QUE ES POTENTIAL ---> usar cada seller de manera particular para no tener que buscarlo a mano etc
    # # TODO: ELIMINAR FALSOS POSITIVOS (available = 0)
    # for edition in editions:
    #     if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
    #         sql = "select ck.edition, ck.name, ck.foil, ck.price as ck, mkm.price as mkm, mkm.seller, mkm.available, (ck.price - mkm.price) as profit, (ck.price - mkm.price) * mkm.available as profittotal, round(ck.price / mkm.price, 2) - 1 profitpct from (select e.code as editioncode, e.name as edition, p.name, foil, round(cast(price * {} as numeric), 2) as price from ck_buylist p left join editions e on p.edition = e.code_ck where e.code = '{}') ck inner join (select e.code as editioncode, e.name as edition, c.name, foil, seller, LEAST(available, 17) as available, round(cast(((price * LEAST(available, 17)) + (select cost from mkm_shippingcosts sc where sc.from = p.itemlocation and sc.itemcount <= LEAST(available, 17) and tracked = p.price >= {} order by itemcount desc limit 1)) / LEAST(available, 17) as numeric), 2) as price from mkm_cardprices p left join mkm_cards c on p.card = c.id and p.edition = c.edition left join editions e on c.edition = e.code_mkm where e.code = '{}') mkm on ck.editioncode = mkm.editioncode and lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where mkm.price < ck.price and round(ck.price / mkm.price, 2) >= {}".format(usdtoeu - comisionporgastosdeenvio, edition["id"], precioparaenviocertificado, edition["id"], profittargetpct)
    #         cards = phppgadmin.query(sql)
    #         with open("output/eutousa.csv", "a", newline='\n') as f:
    #             writer = csv.DictWriter(f, fieldnames=["edition", "name", "foil", "ck", "mkm", "seller", "available", "profit", "profittotal", "profitpct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #             for card in cards:
    #                 print(card)
    #                 writer.writerow(card)
def finance_fromusatoeu():
    editions = Gatherer.getEditions()
    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionmkm = 0.05 # comision que se queda mkm de las ventas
    undercut = 0.05 # undercut para vender
    ajustebeneficio = 0.15 # margen de perdida que asumo al vender de usa a eur (store credit me da 0.3)
    storecreditbonus = 0.3
    with open("output/usatoeu.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["set", "name", "foil", "ck", "mkm", "available"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    # TODO: DEFINIR LO QUE ES POTENTIAL ---> marcar cuando es un staple y etc.
    sql = "select s.name as set, c.name as name, truefalse.value as foil, round(cast(ck.price * {} as numeric), 2) as ck, round(cast(mkm.price * {} as numeric), 2) as mkm, ck.available as available from scr_cards c CROSS JOIN truefalse left join scr_sets s on c.set = s.code left join ck_cardprices ck on c.idck = ck.card and truefalse.value = ck.foil left join mkm_cardpricesmin mkm on c.idmkm = mkm.id and truefalse.value = mkm.foil where (not mkm.name is null and not ck.card is null) and not s.digital and ck.available > 0 and ck.condition = 'NM'".format(usdtoeu, 1 - comisionmkm - undercut)
    cards = phppgadmin.query(sql)
    with open("output/usatoeu.csv", "a", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["set", "name", "foil", "ck", "mkm", "available"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for card in cards:
            card["ck"] = card["ck"].replace(".",",")
            card["mkm"] = card["mkm"].replace(".",",")
            writer.writerow(card)
def finance_dondevendo():
    def obtenseleccion(candidatos, myset):
        if myset == "":
            return None
        else:
            for i, cand in reversed(list(enumerate(candidatos))):
                if cand["set"] == myset or (myset in son and cand["set"] == son[myset]):
                    return cand
                elif (myset in noson and cand["set"] in noson[myset]):
                    candidatos.pop(i)
            if len(candidatos) == 0:
                return None
            elif len(candidatos) == 1:
                return candidatos[0]
            else:
                print(":: {} [{}] ::".format(icard.name, icard.edition))
                for i, cand in list(enumerate(candidatos)):
                    print("{}. {}".format(i, cand["set"]))
                while True:
                    sel = input("Opcion: ")
                    print("")
                    # meterlas todas en noson
                    if sel == "":
                        if not myset in noson:
                            noson[myset] = []
                        noson[myset].extend(candidatos)
                        return None
                    else:
                        sel = (int)(sel)
                        cand = candidatos[sel]
                        son[myset] = cand["set"]
                        return cand

    usdtoeu = ExchangeRate.get("USDEUR=X")
    comisionmkm = 0.05 # comision que se queda mkm de las ventas
    undercut = 0.05 # undercut para vender
    inventory = Deckbox.inventory(True)
    vender = []
    print("Inventario: {} cartas diferentes".format(len(inventory)))
    sql = "select s.name as set, c.name as name, truefalse.value as foil, round(cast(ck.price * {} as numeric), 2) as ck, round(cast(mkm.price * {} as numeric), 2) as mkm from scr_cards c CROSS JOIN truefalse left join scr_sets s on c.set = s.code left join ck_buylist ck on c.idck = ck.card and truefalse.value = ck.foil left join mkm_cardpricesmin mkm on c.idmkm = mkm.id and truefalse.value = mkm.foil where (not mkm.name is null and not ck.card is null) and not s.digital".format(usdtoeu, 1 - comisionmkm - undercut)
    allcards = phppgadmin.query(sql)
    son = {}
    noson = {}
    for icard in inventory:
        for entry in icard.entries:
            # solo comparamos las cartas en ingles
            if (entry.language == "English"):
                candidatos = []
                for card in allcards:
                    if icard.name.lower() == card["name"].lower() and entry.foil == (card["foil"] == "TRUE"):
                        candidatos.append(card)
                seleccion = obtenseleccion(candidatos, icard.edition)
                if not seleccion is None:
                    vender.append(seleccion)

    with open("output/dondevendo.csv", "w", newline='\n') as f:
        writer = csv.DictWriter(f, fieldnames=["set", "name", "foil", "ck", "mkm"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for card in vender:
            card["ck"] = card["ck"].replace(".",",")
            card["mkm"] = card["mkm"].replace(".",",")
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
    print("  8. Donde vendo?")
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
    "7": finance_fromusatoeu,
    "8": finance_dondevendo
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
        input("Finalizado")

#TODO: normalizar datos... puede que no sea necesario una vez tenga lo del scryfall en la db
#select mkm.name as mkmname, ck.name as ckname from mkm_cards mkm left join (select * from ck_cards where edition = 3055) ck on lower(mkm.name) = lower(replace(ck.name, ' - Foil', '')) where mkm.edition = 'Commander+2017' and ck.name is null order by mkm.name
#select ck.name as ckname, mkm.name as mkmname from ck_cards ck left join (select * from mkm_cards where edition = 'Commander+2017') mkm on lower(mkm.name) = lower(replace(ck.name, ' - Foil', '')) where ck.edition = 3055 and mkm.name is null order by ck.name


# TODO: consulta de buylist vs mkm para vender
# select
# 	s.name as set,
# 	c.name as name,
# 	truefalse.value as foil,
# 	round(cast(ck.price * 0.85 as numeric), 2) as ck
# 	--round(cast(mkm.price * 0.9 as numeric), 2) as mkm
# from
# 	scr_cards c CROSS JOIN truefalse
# 	left join scr_sets s on c.set = s.code
# 	left join ck_buylist ck on c.idck = ck.card and truefalse.value = ck.foil
# 	--left join mkm_cardpricesmin mkm on c.idmkm = mkm.edition || '/' || mkm.name and truefalse.value = mkm.foil
# where
# 	--(not mkm.name is null and not ck.card is null)
# 	not s.digital
# 	and not ck.card is null
# order by set,name
#
# select * from ck_buylist where card = 127826
# select * from scr_cards c where not c.idck is null and name like '%Iona%'


# TODO: historico de precios ck
# select id,foil,price,available,timestamp from ck_buylist where id = 213967 and foil
# union
# select id,foil,price,available,timestamp from ck_buylist_history where id = 213967 and foil
# order by timestamp desc
