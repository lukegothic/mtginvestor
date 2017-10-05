from base import CK
from base import MKM
from base import Gatherer
from queue import Queue
import threading
import requests
from base import Proxy
import phppgadmin
import sys
from lxml import html

# proxies = Proxy.getSecure()
#
# def do_work(proxy):
#     try:
#         fullip = "http://{}:{}".format(proxy["ip"], proxy["port"])
#         req = requests.get("https://www.magiccardmarket.eu/", proxies = { "http": fullip, "https": fullip }, timeout = 3)
#         with open(proxy["ip"], "w") as f:
#             print(req, req,text, req.status_code)
#             f.write(req.text)
#     except:
#         print("Proxy {} not working".format(proxy["ip"]))
# def worker():
# 	while True:
# 		item = q.get()
# 		do_work(item)
# 		q.task_done()
#
# q = Queue()
# for i in range(10):
#     t = threading.Thread(target=worker)
#     t.daemon = True
#     t.start()
#
# for proxy in proxies:
#     q.put(proxy)
#
# q.join()

# TODO: RECICLAR ESTO EN EL main.py
# buylist = CK.buylist()
# sql = "INSERT INTO ck_buylist(card,edition,price,foil,count) VALUES"
# for card in buylist:
#     for entry in card.entries:
#         sql = sql + "({},{},{},{},{}),".format(card.id, card.edition, entry.price, "true" if entry.foil else "false", entry.count)
#
# sys.stdout.write("Guardando buylist...")
# sys.stdout.flush()
# phppgadmin.execute(sql[:-1])
# sys.stdout.write("OK")

# TODO: reciclar en el main
# cards = MKM.getCards()
# sql = "INSERT INTO mkm_cards(id,name,edition) VALUES"
# for card in cards:
#     sql += "('{}','{}','{}'),".format(card.id, card.name.replace("'","''"), card.edition)
# phppgadmin.execute(sql[:-1])

#TODO: MOVER A MENU (obtener precios mkm)
editions = MKM.getEditions()
for edition in editions:
    # TODO: controlamos si ya tenemos precios, se puede hacer que solo se controlen precio no actualizados y borrar precios antiguos
    print(edition["name"])
    cnt = phppgadmin.query("select count(*) as c from mkm_cardprices where edition = '{}'".format(edition["id"]))
    if (cnt[0]["c"] == "0"):
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
        else:
            print("No price data")
    else:
        print("Data is present")

#ver precios agrupados
#select c.edition, c.name, p.foil, min(price), sum(available) from mkm_cards c left join mkm_cardprices p on c.edition = p.edition and c.id = p.card where c.edition = 'Alara+Reborn' group by c.name, c.edition, p.foil order by sum(available) asc
