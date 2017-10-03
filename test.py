from base import CK
from base import MKM
from queue import Queue
import threading
import requests
from base import Proxy
import phppgadmin
import sys

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

MKM.getEditions()
